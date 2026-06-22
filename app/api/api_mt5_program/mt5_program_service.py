import asyncio
import logging
import re
from pathlib import Path
from typing import Any, TypedDict

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exception import BusinessException
from app.module.process_module import ProcessModule
from app.postgres.entities.mt5_account_entity import MT5AccountType
from app.postgres.entities.setting_entity import SettingKey
from app.postgres.repositories.mt5_account_repository import mt5_account_repository
from app.postgres.repositories.setting_repository import setting_repository
from app.redis.cache.mt5_program_cache import MT5ProgramCache
from app.setting import settings

logger = logging.getLogger(__name__)


process_module = ProcessModule()


class MT5ProgramDiscover(TypedDict):
    program_name: str
    path: str


class MT5ProgramService:
    async def discover_program_list(self, db: AsyncSession) -> list[MT5ProgramDiscover]:
        path_root_setting = await setting_repository.find_one(
            db=db, filter={"key": SettingKey.MT5_CONTAINER_FOLDER_PATH}
        )
        if not path_root_setting or not path_root_setting.value:
            return []

        path_root = Path(path_root_setting.value)
        if not path_root.exists() or not path_root.is_dir():
            return []

        discover_list: list[MT5ProgramDiscover] = []
        used_names: set[str] = set()
        for folder in sorted([item for item in path_root.iterdir() if item.is_dir()]):
            terminal_path = folder / "terminal64.exe"
            if not terminal_path.exists():
                continue

            normalized = re.sub(r"[^a-zA-Z0-9]+", "_", folder.name.strip()).strip("_")
            base_name = normalized.lower() or "unknown"
            candidate = base_name
            idx = 2
            while candidate in used_names:
                candidate = f"{base_name}_{idx}"
                idx += 1
            used_names.add(candidate)
            discover_list.append(
                {"program_name": candidate, "path": str(terminal_path)}
            )
        return discover_list

    async def refresh_all(self, db: AsyncSession):
        await MT5ProgramCache.clear_cache()

        discover_list = await self.discover_program_list(db)
        for discover in discover_list:
            program_name = discover["program_name"]
            await MT5ProgramCache.program_data_set_path(program_name, discover["path"])
            await MT5ProgramCache.program_log_push(
                program_name, "Refresh MT5 program information..."
            )
        program_name_list = [item["program_name"] for item in discover_list]
        path_list = [item["path"] for item in discover_list]
        await MT5ProgramCache.set_program_name_list(program_name_list)

        mt5_account_list = await mt5_account_repository.find_many(
            db=db,
            filter={"isOpening": 1, "programName": {"IN": program_name_list}},
            sort={"accountType": "ASC"},
        )

        for mt5_account in mt5_account_list:
            program_name = mt5_account.programName
            path = await MT5ProgramCache.program_data_get_path(program_name)
            exe_open_result = await process_module.exe_open(path)
            await MT5ProgramCache.program_data_set_exe_process(
                program_name, exe_open_result["process_info"]
            )
            if exe_open_result["open_new"]:
                await MT5ProgramCache.program_log_push(
                    program_name, f"Open MT5 program {program_name} with path {path}"
                )

            py_open_result = await process_module.py_start(
                program_name, show_terminal=settings.ENV == "development"
            )
            await MT5ProgramCache.program_data_set_py_process(
                program_name, py_open_result["process_info"]
            )

            await MT5ProgramCache.mt5_account_set_by_login_key(
                login_key=mt5_account.accountLogin,
                mt5_account=mt5_account.to_response(),
            )

        await process_module.py_cleanup(program_name_list)
        await process_module.exe_cleanup(path_parent="", path_list_keep=path_list)

    async def open_all(self, db: AsyncSession):
        pass

    async def close_all(self, db: AsyncSession):
        pass

    async def refresh(self, db: AsyncSession, program_name: str):
        pass

    async def open(self, db: AsyncSession, program_name: str) -> dict[str, Any]:
        path = await MT5ProgramCache.program_data_get_path(program_name)
        if not path:
            raise BusinessException(f"Program {program_name} path not found")
        await MT5ProgramCache.program_log_push(program_name, "Open MT5 program...")
        await MT5ProgramCache.program_data_set_account_info(program_name, {"login": 0})
        await mt5_account_repository.update(
            db=db,
            filter={"programName": program_name},
            data={"programName": "", "isOpening": 0},
        )

        exe_open_result = await process_module.exe_open(path)
        await MT5ProgramCache.program_data_set_exe_process(
            program_name, exe_open_result["process_info"]
        )
        py_open_result = await process_module.py_start(
            program_name, show_terminal=settings.ENV == "development"
        )
        await MT5ProgramCache.program_data_set_py_process(
            program_name, py_open_result["process_info"]
        )

        if py_open_result["open_new"]:
            await asyncio.sleep(2)  # Wait a bit for PY to start

        for _ in range(5):
            account_info = await MT5ProgramCache.program_data_get_account_info(
                program_name
            )
            login_Key = account_info.get("login", 0)
            if not login_Key:
                await asyncio.sleep(2)
                continue

            mt5_account_origin = await mt5_account_repository.find_one(
                db=db, filter={"accountLogin": login_Key}
            )
            if not mt5_account_origin:
                await mt5_account_repository.insert_one(
                    db=db,
                    data={
                        "accountType": MT5AccountType.NORMAL,
                        "accountLogin": login_Key,
                        "accountName": account_info.get("name", ""),
                        "accountServer": account_info.get("server", ""),
                        "accountPassword": "",
                        "programName": program_name,
                        "isOpening": 1,
                        "isCopying": 0,
                        "copyMultiplier": 1,
                        "copyMasterLogin": 0,
                        "description": "",
                        "timeCorrectionSeconds": 0,
                    },
                )
            else:
                await mt5_account_repository.update(
                    db=db,
                    filter={"accountLogin": login_Key},
                    data={"programName": program_name, "isOpening": 1, "isCopying": 0},
                )
            mt5_account = await mt5_account_repository.find_one(
                db=db, filter={"accountLogin": login_Key}
            )
            assert mt5_account is not None
            await MT5ProgramCache.mt5_account_set_by_login_key(
                login_key=login_Key,
                mt5_account=mt5_account.to_response(),
            )

        return {"success": True, "program_name": program_name, "exe_path": path}

    async def close(self, db: AsyncSession, program_name: str) -> dict[str, Any]:
        path = await MT5ProgramCache.program_data_get_path(program_name)
        if not path:
            raise BusinessException(f"Program {program_name} path not found")
        await MT5ProgramCache.program_log_push(program_name, "Close MT5 program...")

        exe_process = await MT5ProgramCache.program_data_get_exe_process(program_name)
        py_process = await MT5ProgramCache.program_data_get_py_process(program_name)
        account_info = await MT5ProgramCache.program_data_get_account_info(program_name)

        login_key = account_info.get("login", 0)

        if bool(py_process.get("pid")) and bool(py_process.get("is_running")):
            await process_module.process_stop(py_process["pid"])
        if bool(exe_process.get("pid")) and bool(exe_process.get("is_running")):
            await process_module.process_stop(exe_process["pid"])

        await MT5ProgramCache.program_data_set_account_info(program_name, {"login": 0})
        await MT5ProgramCache.program_data_set_position_list(program_name, [])
        await MT5ProgramCache.program_data_set_exe_process(
            program_name, {"pid": 0, "is_running": False}
        )
        await MT5ProgramCache.program_data_set_py_process(
            program_name, {"pid": 0, "is_running": False}
        )
        await MT5ProgramCache.mt5_account_clear_by_login_key(login_key)

        await mt5_account_repository.update(
            db=db,
            filter={"accountLogin": login_key},
            data={"programName": program_name, "isOpening": 0, "isCopying": 0},
        )

        return {
            "exe_pid": exe_process.get("pid", 0),
            "py_pid": py_process.get("pid", 0),
            "program_name": program_name,
            "exe_path": path,
        }

    async def copy_enabled(self, db: AsyncSession, program_name: str):
        exe_process_follower = await MT5ProgramCache.program_data_get_exe_process(
            program_name
        )
        py_process_follower = await MT5ProgramCache.program_data_get_py_process(
            program_name
        )
        account_info_follower = await MT5ProgramCache.program_data_get_account_info(
            program_name
        )
        login_key_follower = account_info_follower.get("login", 0)
        if not (
            bool(login_key_follower)
            and bool(exe_process_follower.get("pid"))
            and bool(exe_process_follower.get("is_running"))
            and bool(py_process_follower.get("pid"))
            and bool(py_process_follower.get("is_running"))
        ):
            raise BusinessException(f"Program {program_name} is not running")

        mt5_account_follower = await mt5_account_repository.find_one(
            db=db, filter={"accountLogin": login_key_follower}
        )
        if not mt5_account_follower:
            raise BusinessException(
                f"Account follower with login {login_key_follower} not found"
            )
        login_key_master = mt5_account_follower.copyMasterLogin
        if not login_key_master:
            raise BusinessException(
                f"Account follower with login {login_key_follower} has no master login for copying"
            )
        mt5_account_master = await mt5_account_repository.find_one(
            db=db, filter={"accountLogin": login_key_master}
        )
        if not mt5_account_master:
            raise BusinessException(
                f"Account master with login {login_key_master} not found"
            )
        mt5_account_master_dict = mt5_account_master.to_response()
        program_name_master = mt5_account_master_dict["programName"]

        exe_process_master = await MT5ProgramCache.program_data_get_exe_process(
            program_name_master
        )
        py_process_master = await MT5ProgramCache.program_data_get_py_process(
            program_name_master
        )
        if not (
            bool(login_key_master)
            and bool(exe_process_master.get("pid"))
            and bool(exe_process_master.get("is_running"))
            and bool(py_process_master.get("pid"))
            and bool(py_process_master.get("is_running"))
        ):
            raise BusinessException(f"Program {program_name_master} is not running")

        await MT5ProgramCache.program_log_push(
            program_name, f"Enable copying from master account {login_key_master}..."
        )

        await mt5_account_repository.update(
            db,
            filter={"accountLogin": login_key_follower},
            data={"isCopying": 1},
        )
        mt5_account_follower = await mt5_account_repository.find_one(
            db=db, filter={"accountLogin": login_key_follower}
        )
        assert mt5_account_follower is not None
        mt5_account_follower_dict = mt5_account_follower.to_response()

        await MT5ProgramCache.mt5_account_set_by_login_key(
            mt5_account_follower.accountLogin, mt5_account_follower_dict
        )

        return {"copy_status": 1}

    async def copy_disabled(self, db: AsyncSession, program_name: str):
        await MT5ProgramCache.program_log_push(
            program_name, f"Disable copying from program {program_name}..."
        )
        account_info = await MT5ProgramCache.program_data_get_account_info(program_name)
        account_login = account_info.get("login", 0)
        await mt5_account_repository.update(
            db,
            filter={"accountLogin": account_login},
            data={"isCopying": 0},
        )
        mt5_account = await mt5_account_repository.find_one(
            db=db, filter={"accountLogin": account_login}
        )
        if not mt5_account:
            raise BusinessException("MT5 account not found")

        mt5_account_response = mt5_account.to_response()
        await MT5ProgramCache.mt5_account_set_by_login_key(
            mt5_account.accountLogin, mt5_account_response
        )

        return {"isCopying": 0}

    async def setting(self, db: AsyncSession, program_name: str):
        pass

    async def clear_log(self, program_name: str):
        await MT5ProgramCache.program_log_clear(program_name)

    async def clear_error(self, program_name: str):
        await MT5ProgramCache.program_error_clear(program_name)
