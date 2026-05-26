from typing import Any, Optional, TypedDict

from app.socket.socket_constants import SocketMessage
from app.socket.socket_server import sio


class SocketMt5StatusType(TypedDict):
    name: Optional[str]
    pid: Optional[int]
    cpu_percent: float
    memory_mb: float


class SocketMt5Handler:
    @staticmethod
    async def emit_mt5_status(data: SocketMt5StatusType) -> None:
        await sio.emit(SocketMessage.SOCKET_MT5_STATUS, data)  # type: ignore
