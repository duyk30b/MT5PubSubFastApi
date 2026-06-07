import logging

from app.worker.mt5_program_job.mt5_program_job import Mt5ProgramJob

logger = logging.getLogger(__name__)


class AppWorker:
    def __init__(self):
        self.mt5_program_job = Mt5ProgramJob()

    async def start(self):
        await self.mt5_program_job.start()

    async def stop(self):
        await self.mt5_program_job.stop()
