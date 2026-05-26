import logging

from app.worker.mt5_status_job.mt5_status_job import Mt5StatusJob

logger = logging.getLogger(__name__)


class AppWorker:
    def __init__(self):
        self.mt5_status_job = Mt5StatusJob()

    async def start(self):
        await self.mt5_status_job.start()

    async def stop(self):
        await self.mt5_status_job.stop()
