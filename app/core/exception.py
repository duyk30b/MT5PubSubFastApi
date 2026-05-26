from dataclasses import field
from datetime import datetime, timezone
import logging
import traceback
from turtle import st
from typing import Any
from alembic.util import err
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import Request, Response

logger = logging.getLogger(__name__)


class BusinessException(Exception):
    def __init__(
        self,
        message: str,
        *,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        self.status_code = 400
        self.error = "BUSINESS_ERROR"
        self.message = message
        self.details = details
        super().__init__(message)


class AuthenticationException(Exception):
    def __init__(
        self,
        message: str = "Authentication failed",
    ) -> None:
        self.status_code = 401
        self.error = "AUTHENTICATION_ERROR"
        self.message = message
        super().__init__(message)


class TokenExpiredException(Exception):
    def __init__(
        self,
        message: str = "Token expired",
    ) -> None:
        self.status_code = 440
        self.error = "TOKEN_EXPIRED"
        self.message = message
        super().__init__(message)


class AppExceptionHandler:
    @staticmethod
    def build_response(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        method = request.method if hasattr(request, "method") else "N/A"
        path = request.url.path if hasattr(request, "url") else ""
        query = request.url.query if hasattr(request, "url") else ""

        error = getattr(exc, "error", "SERVER_ERROR")
        status_code = getattr(exc, "status_code", None)
        if not isinstance(status_code, int):
            status_code = 500
        message = getattr(exc, "message", str(exc))
        module = f"{type(exc).__module__}.{type(exc).__name__}"
        details = getattr(exc, "details", None)
        error_time = datetime.now(timezone.utc).isoformat(timespec="milliseconds")

        if isinstance(exc, RequestValidationError):
            error = "VALIDATION_ERROR"
            status_code = 422
            details = exc.errors()
            message = "; ".join([f"{err['loc'][-1]}: {err['msg']}" for err in details])
            logger.warning(f"{method} | {status_code} | {path} : {message}")
        elif isinstance(exc, (TokenExpiredException)):
            pass
            # logger.warning(f"{method} | {status_code} | {path} : {message}")
        else:
            logger.error(f"{method} | {status_code} | {path} : {message}")
            traceback.print_exception(exc, limit=-3)

        return JSONResponse(
            status_code=status_code,
            content={
                "time": error_time,
                "statusCode": status_code,
                "error": error,
                "module": module,
                "message": message,
                "request": {
                    "method": method,
                    "path": path,
                    "query": query,
                },
                "details": details,
            },
        )
