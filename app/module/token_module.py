from enum import StrEnum
from typing import TypedDict, cast
from datetime import datetime, timedelta, timezone

from httpx import Auth
from passlib import exc
from app.setting import settings
from jose import ExpiredSignatureError, JWTError, jwt

from app.core.exception import AuthenticationException, TokenExpiredException


class TokenResponse(TypedDict):
    token: str
    exp: int


class TokenPayload(TypedDict):
    userId: int
    clientId: str
    loginTime: float  # timestamp in seconds


class TokenDecoded(TypedDict):
    data: TokenPayload
    iat: int
    exp: int


class TokenExpiredError(Exception):
    pass


class TokenInvalidError(Exception):
    pass


class TokenModule:
    @staticmethod
    def create_access_token(data: TokenPayload) -> TokenResponse:
        now = datetime.now(timezone.utc)
        payload: TokenDecoded = {
            "data": data,
            "iat": int(now.timestamp()),
            "exp": int(
                (now + timedelta(seconds=settings.jwt_access_seconds)).timestamp()
            ),
        }

        token = jwt.encode(
            cast(dict[str, object], payload),
            settings.jwt_access_key,
            algorithm=settings.jwt_algorithm,
        )

        return {
            "token": token,
            "exp": payload["exp"] * 1000,
        }

    @staticmethod
    def create_refresh_token(data: TokenPayload) -> TokenResponse:
        now = datetime.now(timezone.utc)
        payload: TokenDecoded = {
            "data": data,
            "iat": int(now.timestamp()),
            "exp": int(
                (now + timedelta(seconds=settings.jwt_refresh_seconds)).timestamp()
            ),
        }

        token = jwt.encode(
            cast(dict[str, object], payload),
            settings.jwt_refresh_key,
            algorithm=settings.jwt_algorithm,
        )

        return {
            "token": token,
            "exp": payload["exp"] * 1000,
        }

    @staticmethod
    def decode_access_token(token: str) -> TokenDecoded:
        try:
            decoded = jwt.decode(
                token, settings.jwt_access_key, algorithms=[settings.jwt_algorithm]
            )
            return cast(TokenDecoded, decoded)
        except ExpiredSignatureError as exc:
            # raise TokenExpiredError("TOKEN_EXPIRED") from exc
            raise TokenExpiredException("Token expired") from exc
        except JWTError as exc:
            # raise TokenInvalidError("TOKEN_INVALID") from exc
            raise AuthenticationException("Token invalid") from exc

    @staticmethod
    def decode_refresh_token(token: str) -> TokenDecoded:
        try:
            decoded = jwt.decode(
                token, settings.jwt_refresh_key, algorithms=[settings.jwt_algorithm]
            )
            return cast(TokenDecoded, decoded)
        except ExpiredSignatureError as exc:
            raise TokenExpiredError("TOKEN_EXPIRED") from exc
        except JWTError as exc:
            raise TokenInvalidError("TOKEN_INVALID") from exc
