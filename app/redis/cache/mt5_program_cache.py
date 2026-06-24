import asyncio
from datetime import datetime, timezone

from app.module.process_module import ProcessInfo
from app.postgres.entities.mt5_account_entity import MT5AccountAction, MT5AccountDict
from app.redis.model.mt5_program_model import (
    MT5ProgramAccountInfo,
    MT5ProgramData,
    MT5ProgramInfo,
    MT5ProgramPositionInfo,
)
from app.redis.redis_base import RedisBase
from app.utils.py_object import PyObject


def _key_program_name_list() -> str:
    return "mt5:program:name_list"


def _key_mt5_account() -> str:
    return "mt5:mt5_account"


def _key_program_data(program_name: str) -> str:
    return f"mt5:program_data:{program_name}"


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

    async def clear_cache(self, clear_logs: bool = False) -> None:
        program_name_list = await self.get_program_name_list()
        keys_to_delete: list[str] = []

        keys_to_delete.append(_key_program_name_list())
        keys_to_delete.append(_key_mt5_account())

        for program_name in program_name_list:
            keys_to_delete.append(
                _key_program_data(program_name),
            )
            if clear_logs:
                keys_to_delete.extend(
                    [_key_program_log(program_name), _key_program_error(program_name)]
                )

        await self._delete(*keys_to_delete)

    async def program_data_get_all(self, program_name: str) -> MT5ProgramData:
        dataResult = await self._hash_get_all(_key_program_data(program_name))
        if not dataResult:
            return MT5ProgramData(
                path="",
                refresh_time="",
                exe_process={"pid": 0, "is_running": False},
                py_process={"pid": 0, "is_running": False},
                account_info={"login": 0},
                position_list=[],
            )

        return MT5ProgramData(
            path=dataResult.get("path", ""),
            refresh_time=dataResult.get("refresh_time", ""),
            exe_process=PyObject.json_load(
                dataResult.get("exe_process", ""), {"pid": 0, "is_running": False}
            ),
            py_process=PyObject.json_load(
                dataResult.get("py_process", ""), {"pid": 0, "is_running": False}
            ),
            account_info=PyObject.json_load(
                dataResult.get("account_info", ""), {"login": 0}
            ),
            position_list=PyObject.json_load(dataResult.get("position_list", ""), []),
        )

    async def program_get_info(self, program_name: str) -> MT5ProgramInfo:
        program_data = await self.program_data_get_all(program_name)
        login_key = program_data.get("account_info", {}).get("login", 0)

        return MT5ProgramInfo(
            program_name=program_name,
            data=program_data,
            mt5_account=await self.mt5_account_get_by_login_key(login_key),
            error_list=await self.program_error_get_list(program_name),
            log_list=await self.program_log_get_list(program_name),
        )

    async def program_data_get_path(self, program_name: str) -> str:
        result = await self._hash_get(_key_program_data(program_name), "path")
        return result or ""

    async def program_data_get_exe_process(self, program_name: str) -> ProcessInfo:
        result = await self._hash_get(_key_program_data(program_name), "exe_process")
        return PyObject.json_load(result, {})

    async def program_data_get_py_process(self, program_name: str) -> ProcessInfo:
        result = await self._hash_get(_key_program_data(program_name), "py_process")
        return PyObject.json_load(result, {})

    async def program_data_get_account_info(
        self, program_name: str
    ) -> MT5ProgramAccountInfo:
        result = await self._hash_get(_key_program_data(program_name), "account_info")
        return PyObject.json_load(result, {})

    async def program_data_get_position_list(
        self, program_name: str
    ) -> list[MT5ProgramPositionInfo]:
        result = await self._hash_get(_key_program_data(program_name), "position_list")
        return PyObject.json_load(result, [])

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

    async def program_data_set_refresh_time(
        self, program_name: str, refresh_time: str
    ) -> None:
        await self._hash_set(
            _key_program_data(program_name), {"refresh_time": refresh_time}
        )

    async def program_data_set_path(self, program_name: str, path: str) -> None:
        await self._hash_set(_key_program_data(program_name), {"path": path})

    async def program_data_set_exe_process(
        self, program_name: str, exe_process: ProcessInfo
    ) -> None:
        await self._hash_set(
            _key_program_data(program_name),
            {"exe_process": PyObject.json_dump(exe_process)},
        )

    async def program_data_set_py_process(
        self, program_name: str, py_process: ProcessInfo
    ) -> None:
        await self._hash_set(
            _key_program_data(program_name),
            {"py_process": PyObject.json_dump(py_process)},
        )

    async def program_data_set_account_info(
        self, program_name: str, account_info: MT5ProgramAccountInfo
    ) -> None:
        await self._hash_set(
            _key_program_data(program_name),
            {"account_info": PyObject.json_dump(account_info)},
        )

    async def program_data_set_runtime_snapshot(
        self,
        program_name: str,
        refresh_time: str,
        account_info: MT5ProgramAccountInfo,
        position_list: list[MT5ProgramPositionInfo],
    ) -> None:

        # Lỗi với redis version 3.2.3: không hỗ trợ hset với mapping, chỉ hỗ trợ field-value pair. Cần dùng pipeline để batch set nhiều field-value pair.
        # await self._hash_set(
        #     _key_program_data(program_name),
        #     {
        #         "refresh_time": refresh_time,
        #         "account_info": PyObject.json_dump(account_info),
        #         "position_list": PyObject.json_dump(position_list),
        #     },
        # )
        await asyncio.gather(
            self.program_data_set_account_info(program_name, account_info),
            self.program_data_set_position_list(program_name, position_list),
            self.program_data_set_refresh_time(program_name, refresh_time),
        )

    async def program_data_set_position_list(
        self, program_name: str, position_list: list[MT5ProgramPositionInfo]
    ) -> None:
        await self._hash_set(
            _key_program_data(program_name),
            {"position_list": PyObject.json_dump(position_list)},
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
        time_str = (
            datetime.now(timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z")
        )
        message = f"{time_str} - {error_message}"
        print(f"{program_name}: {message}")
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
        time_str = (
            datetime.now(timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z")
        )
        message = f"{time_str} - {log}"
        print(f"{program_name}: {message}")
        async with self._pipeline(transaction=False) as pipe:
            pipe.rpush(key, message)
            pipe.ltrim(key, -200, -1)
            await pipe.execute()

    async def program_log_clear(self, program_name: str) -> None:
        await self._delete(_key_program_log(program_name))

    async def program_error_clear(self, program_name: str) -> None:
        await self._delete(_key_program_error(program_name))

    async def mt5_account_get_by_login_key(self, login_key: int) -> MT5AccountDict:
        result = await self._hash_get(_key_mt5_account(), str(login_key))
        return PyObject.json_load(result, MT5AccountAction.create_response_blank())

    async def mt5_account_set_by_login_key(
        self, login_key: int, mt5_account: MT5AccountDict
    ) -> None:
        await self._hash_set(
            _key_mt5_account(),
            {str(login_key): PyObject.json_dump(mt5_account)},
        )

    async def mt5_account_clear_by_login_key(self, login_key: int) -> None:
        await self._hash_delete(_key_mt5_account(), str(login_key))


MT5ProgramCache = MT5ProgramCacheBase()
