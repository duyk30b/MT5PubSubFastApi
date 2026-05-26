from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.api_auth.auth_request import (
    LoginBody,
    LoginRootBody,
    LogoutBody,
    RefreshTokenBody,
)
from app.api.api_auth.auth_service import AuthService
from app.depends.request_depends import RequestDepends, RequestState
from app.postgres.postgres_connection import PostgresConnection

auth_controller = APIRouter(prefix="/auth", tags=["Auth"])
auth_service = AuthService()


@auth_controller.post("/login")
async def login(
    body: LoginBody,
    state: RequestState = Depends(RequestDepends.state),
    db: AsyncSession = Depends(PostgresConnection.get_db),
) -> dict[str, Any]:
    data = await auth_service.login(state, body, db)
    return data


@auth_controller.post("/login_root")
async def login_root(
    body: LoginRootBody,
    state: RequestState = Depends(RequestDepends.state),
    db: AsyncSession = Depends(PostgresConnection.get_db),
) -> dict[str, Any]:
    data = await auth_service.login_root(state, body, db)
    return data


@auth_controller.post("/refresh_token")
async def refresh_token(
    body: RefreshTokenBody,
    state: RequestState = Depends(RequestDepends.state),
    db: AsyncSession = Depends(PostgresConnection.get_db),
) -> dict[str, Any]:
    data = await auth_service.refresh_token(state, body, db)
    return data


@auth_controller.post("/logout")
async def logout(
    body: LogoutBody,
    state: RequestState = Depends(RequestDepends.state),
    db: AsyncSession = Depends(PostgresConnection.get_db),
):
    data = await auth_service.logout(body)
    return data
