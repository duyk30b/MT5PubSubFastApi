import asyncio
import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.api.api_mt5_program.common.mt5_program_control_process import (
    MT5ProgramControlProcess,
)
from app.api.api_mt5_program.common.mt5_program_refresh import (
    MT5ProgramDiscover,
    MT5ProgramRefresh,
)
from app.core.exception import BusinessException
from app.postgres.entities.mt5_account_entity import MT5AccountAction, MT5AccountDict
from app.postgres.repositories.mt5_account_repository import mt5_account_repository
from app.redis.cache.mt5_program_cache import MT5ProgramCache

logger = logging.getLogger(__name__)


mt5_program_refresh = MT5ProgramRefresh()
mt5_program_control_process = MT5ProgramControlProcess()


class MT5ProgramService:
    async def refresh_all(self, db: Session):
        discover_list = await mt5_program_refresh.discover_program_list(db=db)

        await MT5ProgramCache.clear_cache()

        await MT5ProgramCache.set_program_name_list(
            [item["program_name"] for item in discover_list]
        )

        for item in discover_list:
            program_name = item["program_name"]
            await MT5ProgramCache.program_information_set_path(
                program_name, item["path"]
            )
            await MT5ProgramCache.program_information_set_refresh_time(
                program_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            await MT5ProgramCache.program_log_push(
                program_name, "Refresh MT5 program information..."
            )

        await mt5_program_refresh.refresh_exe_process(discover_list)
        await mt5_program_refresh.refresh_py_process(
            discover_list, terminate_others=True
        )

        mt5_account_list = mt5_account_repository.find_many(db=db, filter={})
        mt5_account_map = {
            account.accountLogin: account for account in mt5_account_list
        }

        await MT5ProgramCache.login_list_add_multiple(
            [account.accountLogin for account in mt5_account_list]
        )

        await asyncio.sleep(2)
        for item in discover_list:
            program_name = item["program_name"]

            exe_process = await MT5ProgramCache.program_information_get_exe_process(
                program_name
            )
            if not exe_process.get("is_running", False):
                continue

            account_info = await MT5ProgramCache.program_information_get_account_info(
                program_name
            )
            id_login = account_info.get("login", 0)
            if not id_login:
                continue

            mt5_account_item = mt5_account_map.get(id_login)
            if mt5_account_item is None:
                continue

            await MT5ProgramCache.account_setting_set_all(
                id_login=id_login,
                program_name=program_name,
                mt5_account=mt5_account_item.to_response(),
            )

        return {"discover_list": discover_list}

    async def open_all(self, db: Session):
        pass

    async def close_all(self, db: Session):
        pass

    async def refresh(self, db: Session, program_name: str):
        pass

    async def open(self, db: Session, program_name: str) -> dict[str, Any]:
        path = await MT5ProgramCache.program_information_get_path(program_name)
        if not path:
            raise BusinessException(f"Program {program_name} path not found")

        discover_list: list[MT5ProgramDiscover] = [
            {"program_name": program_name, "path": path, "exe_pid": 0}
        ]
        await mt5_program_refresh.refresh_exe_process(discover_list)
        await mt5_program_refresh.refresh_py_process(discover_list)

        exe_process = await MT5ProgramCache.program_information_get_exe_process(
            program_name
        )
        if exe_process.get("is_running", False):
            raise BusinessException(
                f"Program {program_name} is running .exe with pid {exe_process.get('pid', 0)}"
            )
        py_process = await MT5ProgramCache.program_information_get_py_process(
            program_name
        )
        if py_process.get("is_running", False):
            raise BusinessException(
                f"Program {program_name} is running .py with pid {py_process.get('pid', 0)}"
            )

        await MT5ProgramCache.program_log_push(program_name, "Open MT5 program...")
        await MT5ProgramCache.program_information_set_copy_status(program_name, False)

        await mt5_program_control_process.exe_open(path)

        await asyncio.sleep(2)  # Đợi một chút để mt5 khởi động

        await mt5_program_control_process.py_start(program_name)
        await asyncio.sleep(2)  # Đợi một chút để python khởi động

        await mt5_program_refresh.refresh_exe_process(discover_list)
        await mt5_program_refresh.refresh_py_process(discover_list)

        for _ in range(5):
            account_info = await MT5ProgramCache.program_information_get_account_info(
                program_name
            )
            login_id = account_info.get("login", 0)
            if not login_id:
                await asyncio.sleep(2)
                continue
            mt5_account = mt5_account_repository.find_one(
                db=db, filter={"accountLogin": login_id}
            )
            await MT5ProgramCache.account_setting_set_all(
                id_login=login_id,
                program_name=program_name,
                mt5_account=mt5_account.to_response()
                if mt5_account
                else MT5AccountAction.create_response_blank(),
            )

        return {"discover_list": discover_list}

    async def close(self, db: Session, program_name: str) -> dict[str, Any]:
        path = await MT5ProgramCache.program_information_get_path(program_name)
        if not path:
            raise BusinessException(f"Program {program_name} path not found")

        discover_list: list[MT5ProgramDiscover] = [
            {"program_name": program_name, "path": path, "exe_pid": 0}
        ]
        await mt5_program_refresh.refresh_exe_process(discover_list)
        await mt5_program_refresh.refresh_py_process(discover_list)

        exe_process = await MT5ProgramCache.program_information_get_exe_process(
            program_name
        )
        py_process = await MT5ProgramCache.program_information_get_py_process(
            program_name
        )
        account_info = await MT5ProgramCache.program_information_get_account_info(
            program_name
        )

        await MT5ProgramCache.program_information_set_copy_status(program_name, False)
        await MT5ProgramCache.program_log_push(program_name, "Close MT5 program...")
        await MT5ProgramCache.account_setting_clear(account_info.get("login", 0))
        await MT5ProgramCache.login_list_remove(account_info.get("login", 0))

        if py_process.get("pid", 0):
            await mt5_program_control_process.py_stop(py_process.get("pid", 0))
        if exe_process.get("pid", 0):
            await mt5_program_control_process.exe_close(exe_process.get("pid", 0))
        await asyncio.sleep(1)

        await mt5_program_refresh.refresh_exe_process(discover_list)
        await mt5_program_refresh.refresh_py_process(discover_list)
        await MT5ProgramCache.program_information_set_account_info(program_name, {})
        await MT5ProgramCache.program_information_set_position_list(program_name, [])

        return {
            "exe_pid": exe_process.get("pid", 0),
            "py_pid": py_process.get("pid", 0),
            "program_name": program_name,
            "exe_path": path,
        }

    async def copy_enabled(self, db: Session, program_name: str):
        account_info_follower = (
            await MT5ProgramCache.program_information_get_account_info(program_name)
        )
        id_login_follower = account_info_follower.get("login", 0)
        if not id_login_follower:
            raise BusinessException(f"Program {program_name} account login not found")

        mt5_account_follower = mt5_account_repository.find_one(
            db=db, filter={"accountLogin": id_login_follower}
        )
        if not mt5_account_follower:
            raise BusinessException(
                f"Account follower with login {id_login_follower} not found"
            )

        id_login_master = mt5_account_follower.copyMasterLogin
        if not id_login_master:
            raise BusinessException(
                f"Account follower with login {id_login_follower} has no master login for copying"
            )
        mt5_account_master = mt5_account_repository.find_one(
            db=db, filter={"accountLogin": id_login_master}
        )
        if not mt5_account_master:
            raise BusinessException(
                f"Account master with login {id_login_master} not found"
            )

        program_name_master = await MT5ProgramCache.account_setting_get_program_name(
            id_login_master
        )
        if not program_name_master:
            raise BusinessException(
                f"Account master with login {id_login_master} has no program name setting"
            )

        exe_process_master = await MT5ProgramCache.program_information_get_exe_process(
            program_name_master
        )
        if not exe_process_master.get("is_running", False):
            raise BusinessException(
                f"Master program {program_name_master} is not running .exe"
            )

        py_process_master = await MT5ProgramCache.program_information_get_py_process(
            program_name_master
        )
        if not py_process_master.get("is_running", False):
            raise BusinessException(
                f"Master program {program_name_master} is not running .py"
            )

        await MT5ProgramCache.program_log_push(
            program_name, f"Enable copying from master account {id_login_master}..."
        )
        await MT5ProgramCache.program_information_set_copy_status(program_name, True)

        return {"copy_status": True}

    async def copy_disabled(self, db: Session, program_name: str):
        await MT5ProgramCache.program_log_push(
            program_name, f"Disable copying from program {program_name}..."
        )
        await MT5ProgramCache.program_information_set_copy_status(program_name, False)

        return {"copy_status": False}

    async def setting(self, db: Session, program_name: str):
        pass

    async def clear_log(self, program_name: str):
        await MT5ProgramCache.program_log_clear(program_name)

    async def clear_error(self, program_name: str):
        await MT5ProgramCache.program_error_clear(program_name)
