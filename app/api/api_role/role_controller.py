from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.api_role.role_service import RoleService
from app.depends.request_depends import RequestDepends, RequestState
from app.postgres.postgres_connection import PostgresConn

role_controller = APIRouter(prefix="/role", tags=["Role"])
role_service = RoleService()


@role_controller.get("/pagination")
async def role_pagination(
    page: int,
    limit: int,
    state: RequestState = Depends(RequestDepends.state),
    db: Session = Depends(PostgresConn.get_db),
) -> dict[str, Any]:
    return await role_service.role_pagination(db, page, limit)
