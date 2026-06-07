from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.api_user.user_request import UserCreateBody, UserUpdateBody
from app.api.api_user.user_service import UserService
from app.depends.request_depends import RequestDepends, RequestState
from app.postgres.postgres_connection import PostgresConn

user_controller = APIRouter(prefix="/user", tags=["User"])
user_service = UserService()


@user_controller.get("/pagination")
async def user_pagination(
    page: int,
    limit: int,
    state: RequestState = Depends(RequestDepends.state),
    db: Session = Depends(PostgresConn.get_db),
) -> dict[str, Any]:
    return await user_service.user_pagination(
        db=db,
        page=page,
        limit=limit,
    )


@user_controller.get("/list")
async def user_list(
    state: RequestState = Depends(RequestDepends.state),
    db: Session = Depends(PostgresConn.get_db),
) -> dict[str, Any]:
    return await user_service.user_list(
        db=db,
    )


@user_controller.get("/detail/{user_id}")
async def user_detail(
    user_id: int,
    state: RequestState = Depends(RequestDepends.state),
    db: Session = Depends(PostgresConn.get_db),
) -> dict[str, Any]:
    return await user_service.user_detail(
        db=db,
        user_id=user_id,
    )


@user_controller.post("/create")
async def user_create(
    body: UserCreateBody,
    state: RequestState = Depends(RequestDepends.state),
    db: Session = Depends(PostgresConn.get_db),
) -> dict[str, Any]:
    return await user_service.user_create(
        db=db,
        body=body,
    )


@user_controller.post("/update/{user_id}")
async def user_update(
    user_id: int,
    body: UserUpdateBody,
    state: RequestState = Depends(RequestDepends.state),
    db: Session = Depends(PostgresConn.get_db),
) -> dict[str, Any]:
    return await user_service.user_update(
        db=db,
        user_id=user_id,
        body=body,
    )


@user_controller.post("/destroy/{user_id}")
async def user_destroy(
    user_id: int, db: Session = Depends(PostgresConn.get_db)
) -> dict[str, Any]:
    return await user_service.user_destroy(db=db, user_id=user_id)


@user_controller.post("/force-logout/{user_id}")
async def user_force_logout(user_id: int) -> dict[str, Any]:
    return await user_service.user_force_logout(user_id=user_id)
