from typing import Any

from app.socket.socket_constants import SocketMessage
from app.socket.socket_server import sio


# client emit: "demo:send"
@sio.on(SocketMessage.DEMO_SEND)  # type: ignore
async def handle_demo_send(sid: str, data: Any) -> None:
    print("Received demo:", data)

    # reply lại client
    await sio.emit(SocketMessage.DEMO_RESPONSE, {"msg": "hello từ server"}, to=sid)  # type: ignore


# server chủ động emit (function dùng trong code khác)
async def emit_demo() -> None:
    await sio.emit(SocketMessage.DEMO_PUSH, {"msg": "server push"})  # type: ignore
