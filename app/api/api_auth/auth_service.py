from datetime import datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.api_auth.auth_request import (
    LoginBody,
    LoginRootBody,
    LogoutBody,
    RefreshTokenBody,
)
from app.core.security import verify_password
from app.depends.request_depends import RequestState
from app.module.token_module import TokenModule, TokenPayload
from app.postgres.entities.user_entity import UserType
from app.postgres.repositories.user_repository import user_repository
from app.redis.cache.user_login_cache import userLoginCache


class AuthService:
    def __init__(self):
        pass

    async def login(
        self, state: RequestState, body: LoginBody, db: AsyncSession
    ) -> dict[str, Any]:
        clientId = state["clientId"]
        user = await user_repository.find_one(db, filter={"username": body.username})
        if not user:
            raise HTTPException(status_code=401, detail="Invalid username")

        if user.isActive == 0:
            raise HTTPException(status_code=403, detail="User is inactive")

        if not verify_password(body.password, user.passwordHash):
            raise HTTPException(status_code=401, detail="Invalid password")

        token_payload: TokenPayload = {
            "userId": user.id,
            "clientId": clientId,
            "loginTime": datetime.now().timestamp(),
        }

        try:
            accessToken = TokenModule.create_access_token(token_payload)
            refreshToken = TokenModule.create_refresh_token(token_payload)
        except ValueError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc

        await userLoginCache.login(user.id, clientId, token_payload["loginTime"])

        return {
            "user": {
                "id": user.id,
                "username": user.username,
            },
            "accessToken": accessToken["token"],
            "accessExp": accessToken["exp"],
            "refreshToken": refreshToken["token"],
            "refreshExp": refreshToken["exp"],
        }

    async def login_root(
        self, state: RequestState, body: LoginRootBody, db: AsyncSession
    ) -> dict[str, Any]:
        clientId = state["clientId"]
        userRoot = await user_repository.find_one(
            db, filter={"username": body.username}
        )

        if not userRoot or userRoot.userType != UserType.ROOT or not userRoot.isActive:
            raise HTTPException(status_code=401, detail="Invalid user")

        if not verify_password(body.password, userRoot.passwordHash):
            raise HTTPException(status_code=401, detail="Invalid password")

        user = await user_repository.find_one(db, filter={"id": body.userId})
        if not user:
            raise HTTPException(status_code=401, detail="Invalid userId")

        token_payload: TokenPayload = {
            "userId": user.id,
            "clientId": clientId,
            "loginTime": datetime.now().timestamp(),
        }

        accessToken = TokenModule.create_access_token(token_payload)
        refreshToken = TokenModule.create_refresh_token(token_payload)

        await userLoginCache.login(user.id, clientId, token_payload["loginTime"])
        return {
            "user": {
                "id": user.id,
                "username": user.username,
            },
            "accessToken": accessToken["token"],
            "accessExp": accessToken["exp"],
            "refreshToken": refreshToken["token"],
            "refreshExp": refreshToken["exp"],
        }

    async def refresh_token(
        self, state: RequestState, body: RefreshTokenBody, db: AsyncSession
    ) -> dict[str, Any]:
        clientId = state["clientId"]
        try:
            decoded_token = TokenModule.decode_refresh_token(body.refreshToken)
            userId = decoded_token["data"]["userId"]
        except Exception as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc

        if userId == 0:
            raise HTTPException(status_code=401, detail="Invalid token")

        if not await userLoginCache.check_client(
            userId, clientId, decoded_token["data"]["loginTime"]
        ):
            raise HTTPException(
                status_code=401, detail="Refresh token has been revoked"
            )

        user = await user_repository.find_one(db, filter={"id": userId})
        if not user:
            raise HTTPException(status_code=401, detail="Invalid userId")

        if user.isActive == 0:
            raise HTTPException(status_code=403, detail="User is inactive")

        token_payload: TokenPayload = {
            "userId": user.id,
            "clientId": clientId,
            "loginTime": decoded_token["data"]["loginTime"],
        }

        try:
            accessToken = TokenModule.create_access_token(token_payload)
        except ValueError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc

        return {
            "user": {
                "id": user.id,
            },
            "accessToken": accessToken["token"],
            "accessExp": accessToken["exp"],
        }

    async def logout(
        self,
        body: LogoutBody,
    ):
        payload = TokenModule.decode_refresh_token(body.refreshToken)
        userId: int = payload["data"]["userId"]
        clientId: str = payload["data"].get("clientId", "").strip()
        loginTime: float = payload["data"].get("loginTime", 0.0)

        await userLoginCache.logout(userId, clientId, loginTime)

        return {"message": "Logout successful"}
