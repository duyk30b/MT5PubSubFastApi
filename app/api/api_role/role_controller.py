from typing import Any

from fastapi import APIRouter

role_controller = APIRouter(prefix="/role", tags=["Role"])


@role_controller.get("/pagination")
async def role_pagination():
    return {"message": "pagination of Role"}


@role_controller.get("/list")
async def role_list() -> dict[str, list[Any]]:
    return {"roleList": []}
