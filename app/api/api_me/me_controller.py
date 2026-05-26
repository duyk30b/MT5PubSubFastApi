from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.depends.request_depends import RequestDepends
from app.postgres.entities.user_entity import UserEntity
from app.postgres.postgres_connection import PostgresConnection

me_controller = APIRouter(prefix="/me", tags=["Me"])


@me_controller.get("/data")
async def get_data(
    userId: int = Depends(RequestDepends.require_auth),
    db: AsyncSession = Depends(PostgresConnection.get_db),
) -> dict[str, Any]:
    user = await db.get(UserEntity, userId)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "userType": user.userType,
        },
        "permissionIds": [1, 2, 3],
        "permissionAll": [],
    }
