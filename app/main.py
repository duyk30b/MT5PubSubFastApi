from contextlib import asynccontextmanager
import asyncio
import logging
from math import log
import socketio
from app.core.exception import AppExceptionHandler
from app.core.middleware import AppMiddleware
from app.socket.socket_server import sio
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from app.api.api_auth.auth_controller import auth_controller
from app.api.api_me.me_controller import me_controller
from app.api.api_setting.setting_controller import setting_controller
from app.api.api_user.user_controller import user_controller
from app.api.api_role.role_controller import role_controller
from app.api.api_user_role.user_role_controller import user_role_controller
from app.mongo.mongo_connection import mongodb
from app.postgres.postgres_connection import pgConn
from app.redis.redis_connection import redisConnection
from app.worker.worker import AppWorker
import app.socket.socket_events  # register socket handlers
from app.core.logger import ColorFormatter
from app.setting import settings

logger = logging.getLogger(__name__)
app_worker = AppWorker()


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        await asyncio.gather(
            pgConn.connect(),
            mongodb.connect(),
            redisConnection.connect(),
        )
        await app_worker.start()
        # log document link /docs and /redoc
        logger.info("API docs link: http://localhost:{}/docs".format(settings.api_port))
        logger.info("API redoc link: http://localhost:{}/redoc".format(settings.api_port))
    except Exception as exc:
        logger.error(
            f"Application startup failed: {type(exc).__module__}.{type(exc).__name__}: {str(exc)}"
        )
        # traceback.print_exception(exc, limit=-3)
        raise RuntimeError(str(exc)) from None

    yield

    await app_worker.stop()

    await asyncio.gather(
        mongodb.close(),
        redisConnection.close(),
    )
    pgConn.close()


fast_app = FastAPI(lifespan=lifespan)


fast_app.add_middleware(AppMiddleware)
# CORSMiddleware cần khai báo cuối cùng, để cho client đọc response, bất kể statusCode là gì
fast_app.add_middleware(
    CORSMiddleware,
    # allow_origins=[
    #     "http://localhost:5174",
    #     "http://127.0.0.1:5174",
    #     "http://192.168.1.21:5174",
    # ],
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

fast_app.include_router(setting_controller)
fast_app.include_router(auth_controller)
fast_app.include_router(me_controller)
fast_app.include_router(user_controller)
fast_app.include_router(role_controller)
fast_app.include_router(user_role_controller)

fast_app.add_exception_handler(
    RequestValidationError, AppExceptionHandler.build_response
)


@fast_app.get("/")
async def root():
    return {"message": "Hello World"}


socket_app = socketio.ASGIApp(sio, other_asgi_app=fast_app)
