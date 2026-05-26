import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass(order=True)
class QueueJob:
    priority: int
    seq: int
    data: Any = field(compare=False)
    retries: int = field(default=0, compare=False)
    max_retries: int = field(default=3, compare=False)


class QueueStatus(IntEnum):
    Init = 0
    Running = 1
    Stop = 2


class AppQueue(ABC):
    def __init__(self, name: str = "AppQueue", maxsize: int = 100) -> None:
        self._name = name
        self._queue: asyncio.PriorityQueue[QueueJob] = asyncio.PriorityQueue(
            maxsize=maxsize
        )
        self._task: Optional[asyncio.Task[None]] = None
        self._status = QueueStatus.Init
        self._seq = 0
        self._background_tasks: set[asyncio.Task[None]] = set()

    def start(self) -> None:
        if self._status != QueueStatus.Init:
            return
        self._status = QueueStatus.Running
        self._task = asyncio.create_task(self._run(), name=self._name)

    async def _run(self) -> None:
        try:
            while self._status == QueueStatus.Running:
                job = await self._queue.get()
                if job.data is None:
                    self._queue.task_done()
                    break
                try:
                    await self.execute_job(job)
                except asyncio.TimeoutError:
                    logger.error(f"[TIMEOUT] {job.data}")
                    await self._handle_retry(job)
                except asyncio.CancelledError:
                    logger.warning(f"[Cancelled] {job.data}")
                    raise  # ⚠️ phải raise lại để đảm bảo task được dọn dẹp đúng cách
                except Exception as e:
                    logger.exception(f"[ERROR] {job.data}: {e}")
                    await self._handle_retry(job)
                finally:
                    self._queue.task_done()
        finally:
            self._status = QueueStatus.Stop

    async def _handle_retry(self, job: QueueJob) -> None:
        if self._status != QueueStatus.Running:
            return

        if len(self._background_tasks) > 100:
            logger.warning("Too many background tasks")
            return

        if job.retries >= job.max_retries:
            return
        job.retries += 1
        delay = min(2**job.retries, 60)

        task = asyncio.create_task(self._requeue_with_delay(job, delay))
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    async def _requeue_with_delay(self, job: QueueJob, delay: int) -> None:
        if self._status != QueueStatus.Running:
            return
        await asyncio.sleep(delay)
        self._seq += 1
        job.seq = self._seq
        # await self._queue.put(job)
        # await asyncio.wait_for(self._queue.put(job), timeout=5)
        try:
            self._queue.put_nowait(job)
        except asyncio.QueueFull:
            logger.warning("Retry dropped due to full queue")

    async def add(self, data: Any, priority: int = 10, max_retries: int = 3) -> None:
        if self._status != QueueStatus.Running:
            raise RuntimeError("Queue not running")
        self._seq += 1
        await self._queue.put(
            QueueJob(
                priority=priority, seq=self._seq, data=data, max_retries=max_retries
            )
        )

    async def remove(self, data: Any) -> None:
        if self._status != QueueStatus.Running:
            raise RuntimeError("Queue not running")

    async def stop(self) -> None:
        if self._status != QueueStatus.Running:
            return
        await self._queue.join()  # Wait until all items have been processed
        await self._queue.put(
            QueueJob(priority=0, seq=0, data=None, max_retries=0)
        )  # Signal the worker to stop
        if self._task:
            await self._task

    async def force_stop(self) -> None:  # Dừng ngay lập tức (không chờ queue)
        self._status = QueueStatus.Stop
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        for t in self._background_tasks:
            t.cancel()
        await asyncio.gather(*self._background_tasks, return_exceptions=True)
        self._background_tasks.clear()

    async def wait_until_empty(self) -> None:
        await self._queue.join()  # Wait until all items have been processed

    def get_queue_size(self) -> int:
        return self._queue.qsize()

    def is_empty(self) -> bool:
        return self._queue.empty()

    @abstractmethod
    async def execute_job(self, job: QueueJob) -> None:
        raise NotImplementedError
