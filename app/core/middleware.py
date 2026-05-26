from datetime import datetime, timezone
from math import log
import time as time_module
from typing import Awaitable, Callable
import traceback
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exception import AppExceptionHandler, AuthenticationException
from app.module.token_module import TokenModule
from app.redis.cache.user_data_cache import userDataCache
from app.redis.cache.user_login_cache import userLoginCache
import logging

logger = logging.getLogger(__name__)


class AppMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ):
        if request.method == "OPTIONS" or request.url.path in [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]:
            return await call_next(request)

        clientId = request.headers.get("X-Client-Id", "").strip()
        authorization = request.headers.get("Authorization", "")

        request.state.clientId = clientId
        request.state.ip = request.client.host if request.client else ""
        request.state.userId = None
        time_start_second = time_module.time()
        time_start_string = datetime.fromtimestamp(
            time_start_second, timezone.utc
        ).isoformat()

        # TODO: Throttle login attempts to prevent brute-force attacks
        # TODO: Block IP
        # TODO: Log: pprint or log to file or log to ELK stack

        try:
            if authorization.startswith("Bearer "):
                accessToken = authorization.replace("Bearer ", "", 1).strip()
                if accessToken:
                    payload = TokenModule.decode_access_token(accessToken)
                    userId: int = payload["data"]["userId"]
                    tokenClientId = payload["data"].get("clientId", "").strip()
                    tokenLoginTime = payload["data"].get("loginTime", 0.0)
                    request.state.userId = userId

                    if clientId != tokenClientId:
                        raise AuthenticationException(
                            "Token invalid: ClientID does not match token."
                        )

                    if not await userLoginCache.check_client(
                        userId, clientId, tokenLoginTime
                    ):
                        raise AuthenticationException("Token invalid: Token revoked.")

                    userCache = await userDataCache.get_user(userId)
                    if userCache and not userCache["isActive"]:
                        raise AuthenticationException("User is inactive.")

            response = await call_next(request)
            time_end_second = time_module.time()
            time_end_string = datetime.fromtimestamp(
                time_end_second, timezone.utc
            ).isoformat()
            duration = time_end_second - time_start_second
            response.headers["X-Time-Start"] = time_start_string
            response.headers["X-Time-Duration"] = str(duration * 1000) + "ms"
            response.headers["X-Time-End"] = time_end_string
            print(
                f"{request.method} | {request.url} | {request.state.ip} | {request.state.userId} - {duration:.3f}s"
            )
            return response
        except Exception as exc:
            return AppExceptionHandler.build_response(request, exc)
