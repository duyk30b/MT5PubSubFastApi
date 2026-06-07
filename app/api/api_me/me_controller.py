from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.depends.request_depends import RequestDepends
from app.postgres.entities.user_entity import UserEntity, UserType
from app.postgres.postgres_connection import PostgresConn

me_controller = APIRouter(prefix="/me", tags=["Me"])


@me_controller.get("/data")
async def get_data(
    userId: int = Depends(RequestDepends.require_auth),
    db: Session = Depends(PostgresConn.get_db),
) -> dict[str, Any]:
    user = db.query(UserEntity).filter(UserEntity.id == userId).first()
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
