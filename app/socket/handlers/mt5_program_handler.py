from app.redis.model.mt5_program_model import MT5ProgramData
from app.socket.socket_constants import SocketMessage
from app.socket.socket_server import sio
from app.utils.py_class import PyClass


class SocketMT5ProgramInfo(PyClass):
    event_time: str
    mt5_program_info_list: list[MT5ProgramData]


class SocketMt5Handler:
    @staticmethod
    async def emit_mt5_program_info(data: SocketMT5ProgramInfo) -> None:
        data_dict = data.to_dict()
        await sio.emit(SocketMessage.SOCKET_MT5_PROGRAM_INFO, data_dict)  # pyright: ignore[reportUnknownMemberType]
