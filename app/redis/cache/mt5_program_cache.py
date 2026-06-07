import time

from app.postgres.entities.mt5_account_entity import MT5AccountAction, MT5AccountDict
from app.redis.model.mt5_program_model import (
    MT5ProgramAccountInfo,
    MT5ProgramAccountSetting,
    MT5ProgramData,
    MT5ProgramInformation,
    MT5ProgramPositionInfo,
    MT5ProgramProcessInfo,
)
from app.redis.redis_base import RedisBase
from app.utils.py_object import PyObject


def _key_program_name_list() -> str:
    return "mt5:program:name_list"


def _key_login_list() -> str:
    return "mt5:program:login_list"


def _key_account_setting(id_login: int) -> str:
    return f"mt5:account_setting:{id_login}"


def _key_program_information(program_name: str) -> str:
    return f"mt5:program_information:{program_name}"


def _key_program_log(program_name: str) -> str:
    return f"mt5:program_log:{program_name}:log"


def _key_program_error(program_name: str) -> str:
    return f"mt5:program_error:{program_name}:error"


class MT5ProgramCacheBase(RedisBase):
    async def get_program_name_list(self) -> list[str]:
        result = await self._set_get_member_list(_key_program_name_list())
        return sorted(result)

    async def set_program_name(self, program_name: str) -> None:
        await self._set_add(_key_program_name_list(), program_name)

    async def set_program_name_list(self, program_name_list: list[str]) -> None:
        if not program_name_list:
            return
        await self._set_add(_key_program_name_list(), *program_name_list)

    async def login_list_get_all(self) -> list[int]:
        result = await self._set_get_member_list(_key_login_list())
        return [int(login) for login in result]

    async def login_list_add(self, id_login: int) -> None:
        await self._set_add(_key_login_list(), str(id_login))

    async def login_list_add_multiple(self, id_login_list: list[int]) -> None:
        if not id_login_list:
            return
        await self._set_add(_key_login_list(), *map(str, id_login_list))

    async def login_list_remove(self, id_login: int) -> None:
        await self._set_remove(_key_login_list(), str(id_login))

    async def clear_cache(self, clear_logs: bool = False) -> None:
        program_name_list = await self.get_program_name_list()
        id_login_list = await self.login_list_get_all()
        keys_to_delete: list[str] = []

        keys_to_delete.append(_key_program_name_list())
        keys_to_delete.append(_key_login_list())

        for program_name in program_name_list:
            keys_to_delete.append(
                _key_program_information(program_name),
            )
            if clear_logs:
                keys_to_delete.extend(
                    [_key_program_log(program_name), _key_program_error(program_name)]
                )

        for id_login in id_login_list:
            keys_to_delete.append(_key_account_setting(id_login))

        await self._delete(*keys_to_delete)

    async def program_information_get_all(
        self, program_name: str
    ) -> MT5ProgramInformation:
        infoResult = await self._hash_get_all(_key_program_information(program_name))
        if not infoResult:
            raise Exception(f"Program {program_name} information not found")

        return MT5ProgramInformation(
            path=infoResult.get("path", ""),
            refresh_time=infoResult.get("refresh_time", ""),
            exe_process=PyObject.json_load(infoResult.get("exe_process", ""), {}),
            py_process=PyObject.json_load(infoResult.get("py_process", ""), {}),
            account_info=PyObject.json_load(infoResult.get("account_info", ""), {}),
            position_list=PyObject.json_load(infoResult.get("position_list", ""), []),
            copy_enabled=infoResult.get("copy_status", "0") == "1",
        )

    async def program_get_data(self, program_name: str) -> MT5ProgramData:
        program_information = await self.program_information_get_all(program_name)
        id_login = program_information.get("account_info", {}).get("login", 0)

        return MT5ProgramData(
            program_name=program_name,
            information=program_information,
            account_setting=await self.account_setting_get_all(id_login),
            error_list=await self.program_error_get_list(program_name),
            log_list=await self.program_log_get_list(program_name),
        )

    async def program_information_get_path(self, program_name: str) -> str:
        result = await self._hash_get(_key_program_information(program_name), "path")
        return result or ""

    async def program_information_get_exe_process(
        self, program_name: str
    ) -> MT5ProgramProcessInfo:
        result = await self._hash_get(
            _key_program_information(program_name), "exe_process"
        )
        return PyObject.json_load(result, {})

    async def program_information_get_py_process(
        self, program_name: str
    ) -> MT5ProgramProcessInfo:
        result = await self._hash_get(
            _key_program_information(program_name), "py_process"
        )
        return PyObject.json_load(result, {})

    async def program_information_get_account_info(
        self, program_name: str
    ) -> MT5ProgramAccountInfo:
        result = await self._hash_get(
            _key_program_information(program_name), "account_info"
        )
        return PyObject.json_load(result, {})

    async def program_information_get_position_list(
        self, program_name: str
    ) -> list[MT5ProgramPositionInfo]:
        result = await self._hash_get(
            _key_program_information(program_name), "position_list"
        )
        return PyObject.json_load(result, [])

    async def program_information_get_copy_status(self, program_name: str) -> bool:
        result = await self._hash_get(
            _key_program_information(program_name), "copy_status"
        )
        return result == "1"

    async def program_log_get_list(
        self, program_name: str, length: int = 10
    ) -> list[str]:
        # result = await self._list_range(_key_program_log(program_name), 0, length - 1)
        result = await self._list_range(_key_program_log(program_name), -length, -1)
        return result

    async def program_error_get_list(
        self, program_name: str, length: int = 10
    ) -> list[str]:
        # result = await self._list_range(_key_program_error(program_name), 0, length - 1)
        result = await self._list_range(_key_program_error(program_name), -length, -1)
        return result

    async def account_setting_get_mt5_account(self, id_login: int) -> MT5AccountDict:
        result = await self._hash_get(_key_account_setting(id_login), "mt5_account")
        return PyObject.json_load(result, {})

    async def account_setting_get_program_name(self, id_login: int) -> str:
        result = await self._hash_get(_key_account_setting(id_login), "program_name")
        return result or ""

    async def account_setting_get_all(self, id_login: int) -> MT5ProgramAccountSetting:
        result = await self._hash_get_all(_key_account_setting(id_login))
        mt5_account_blank = MT5AccountAction.create_response_blank()
        if not result:
            return MT5ProgramAccountSetting(
                program_name="", mt5_account=mt5_account_blank
            )

        return MT5ProgramAccountSetting(
            program_name=result.get("program_name", ""),
            mt5_account=PyObject.json_load(
                result.get("mt5_account", ""), mt5_account_blank
            ),
        )

    async def program_information_set_refresh_time(
        self, program_name: str, refresh_time: str
    ) -> None:
        await self._hash_set(
            _key_program_information(program_name),
            {"refresh_time": refresh_time},
        )

    async def program_information_set_path(self, program_name: str, path: str) -> None:
        await self._hash_set(
            _key_program_information(program_name),
            {"path": path},
        )

    async def program_information_set_exe_process(
        self, program_name: str, exe_process: MT5ProgramProcessInfo
    ) -> None:
        await self._hash_set(
            _key_program_information(program_name),
            {"exe_process": PyObject.json_dump(exe_process)},
        )

    async def program_information_set_py_process(
        self, program_name: str, py_process: MT5ProgramProcessInfo
    ) -> None:
        await self._hash_set(
            _key_program_information(program_name),
            {"py_process": PyObject.json_dump(py_process)},
        )

    async def program_information_set_account_info(
        self, program_name: str, account_info: MT5ProgramAccountInfo
    ) -> None:
        await self._hash_set(
            _key_program_information(program_name),
            {"account_info": PyObject.json_dump(account_info)},
        )

    async def program_information_set_runtime_snapshot(
        self,
        program_name: str,
        refresh_time: str,
        account_info: MT5ProgramAccountInfo,
        position_list: list[MT5ProgramPositionInfo],
    ) -> None:
        # Batch runtime fields in one Redis hash write to reduce per-loop latency.
        await self._hash_set(
            _key_program_information(program_name),
            {
                "refresh_time": refresh_time,
                "account_info": PyObject.json_dump(account_info),
                "position_list": PyObject.json_dump(position_list),
            },
        )

    async def program_information_set_position_list(
        self, program_name: str, position_list: list[MT5ProgramPositionInfo]
    ) -> None:
        await self._hash_set(
            _key_program_information(program_name),
            {"position_list": PyObject.json_dump(position_list)},
        )

    async def program_information_set_copy_status(
        self, program_name: str, copy_status: bool
    ) -> None:
        await self._hash_set(
            _key_program_information(program_name),
            {"copy_status": "1" if copy_status else "0"},
        )

    async def program_error_push(self, program_name: str, error_message: str) -> None:
        # await self._list_push_head(
        #     _key_program_error(program_name),
        #     f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {error_message}",
        # )
        # await self._list_trim(
        #     _key_program_error(program_name), 0, 100
        # )  # Keep only the latest 100 errors

        key = _key_program_error(program_name)
        message = f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {error_message}"
        async with self._pipeline(transaction=False) as pipe:
            pipe.rpush(key, message)
            pipe.ltrim(key, -100, -1)
            await pipe.execute()

    async def program_log_push(self, program_name: str, log: str) -> None:
        # await self._list_push_head(
        #     _key_program_log(program_name),
        #     f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {log}",
        # )
        # await self._list_trim(
        #     _key_program_log(program_name), 0, 200
        # )  # Keep only the latest 200 logs

        key = _key_program_log(program_name)
        message = f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {log}"
        async with self._pipeline(transaction=False) as pipe:
            pipe.rpush(key, message)
            pipe.ltrim(key, -200, -1)
            await pipe.execute()

    async def program_log_clear(self, program_name: str) -> None:
        await self._delete(_key_program_log(program_name))

    async def program_error_clear(self, program_name: str) -> None:
        await self._delete(_key_program_error(program_name))

    async def account_setting_set_mt5_account(
        self, id_login: int, mt5_account: MT5AccountDict
    ) -> None:
        await self._hash_set(
            _key_account_setting(id_login),
            {"mt5_account": PyObject.json_dump(mt5_account)},
        )

    async def account_setting_set_program_name(
        self, id_login: int, program_name: str
    ) -> None:
        await self._hash_set(
            _key_account_setting(id_login),
            {"program_name": program_name},
        )

    async def account_setting_set_all(
        self,
        id_login: int,
        program_name: str,
        mt5_account: MT5AccountDict,
    ) -> None:
        await self._hash_set(
            _key_account_setting(id_login),
            {
                "program_name": program_name,
                "mt5_account": PyObject.json_dump(mt5_account),
            },
        )

    async def account_setting_clear(self, id_login: int) -> None:
        await self._delete(_key_account_setting(id_login))


MT5ProgramCache = MT5ProgramCacheBase()
