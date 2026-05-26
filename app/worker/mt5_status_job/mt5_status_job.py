import asyncio

from app.worker.mt5_status_job.mt5_process_information import mt5_process_information
from app.socket.handlers.mt5_handler import SocketMt5Handler


class Mt5StatusJob:
    def __init__(self):
        self._task: asyncio.Task[None] | None = None
        self._interval_seconds = 2

    async def _run(self):
        while True:
            process_status = mt5_process_information.get_proc_status()
            await SocketMt5Handler.emit_mt5_status(
                data={
                    "name": process_status["name"],
                    "pid": process_status["pid"],
                    "cpu_percent": process_status["cpu_percent"],
                    "memory_mb": process_status["memory_mb"],
                },
            )
            await asyncio.sleep(self._interval_seconds)

    async def start(self):
        if self._task is not None and not self._task.done():
            return
        self._task = asyncio.create_task(self._run(), name="mt5_status_job")

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
