from typing import Any
from fastapi import APIRouter

user_role_controller = APIRouter(prefix="/user_role", tags=["UserRole"])


@user_role_controller.get("/pagination")
async def user_role_pagination():
    return {"message": "pagination of UserRole"}


@user_role_controller.get("/list")
async def user_role_list() -> dict[str, list[Any]]:
    return {"userRoleList": []}
