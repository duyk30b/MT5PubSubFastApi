# import để register, chỉ cần import → decorator @sio.on(...) sẽ tự đăng ký
from app.socket.handlers import (
    demo_handler,  # type: ignore  # noqa: F401
    mt5_program_handler,  # type: ignore  # noqa: F401
)
