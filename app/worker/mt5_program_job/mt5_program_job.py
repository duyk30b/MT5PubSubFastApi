import asyncio
import logging
from datetime import datetime, timezone

from app.redis.cache.mt5_program_cache import MT5ProgramCache
from app.redis.model.mt5_program_model import MT5ProgramInfo
from app.socket.handlers.mt5_program_handler import (
    SocketMt5Handler,
    SocketMT5ProgramInfo,
)

logger = logging.getLogger(__name__)


class Mt5ProgramJob:
    def __init__(self):
        self._task: asyncio.Task[None] | None = None
        self._interval_seconds = 0.5

    async def _run(self):
        while True:
            try:
                program_name_list = await MT5ProgramCache.get_program_name_list()
                mt5_program_info_list: list[MT5ProgramInfo] = []
                for program_name in program_name_list:
                    mt5_program_info = await MT5ProgramCache.program_get_info(
                        program_name
                    )
                    mt5_program_info_list.append(mt5_program_info)

                await SocketMt5Handler.emit_mt5_program_info(
                    data=SocketMT5ProgramInfo(
                        event_time=(
                            datetime.now(timezone.utc)
                            .isoformat(timespec="milliseconds")
                            .replace("+00:00", "Z")
                        ),
                        mt5_program_info_list=mt5_program_info_list,
                    )
                )
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Unhandled exception in mt5_program_job loop")
            await asyncio.sleep(self._interval_seconds)

    async def start(self):
        if self._task is not None and not self._task.done():
            return
        self._task = asyncio.create_task(self._run(), name="mt5_program_job")

    async def stop(self):
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        finally:
            self._task = None
