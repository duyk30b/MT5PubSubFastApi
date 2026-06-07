from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.api_mt5_account.mt5_account_request import (
    Mt5AccountCreateBody,
    Mt5AccountQuery,
    Mt5AccountUpdateBody,
)
from app.api.api_mt5_account.mt5_account_service import Mt5AccountService
from app.depends.request_depends import RequestDepends, RequestState
from app.postgres.postgres_connection import PostgresConn

mt5_account_controller = APIRouter(prefix="/mt5_account", tags=["MT5 Account"])
mt5_account_service = Mt5AccountService()


@mt5_account_controller.get("/list")
async def mt5_account_list(
    state: RequestState = Depends(RequestDepends.state),
    db: Session = Depends(PostgresConn.get_db),
) -> dict[str, Any]:
    return await mt5_account_service.mt5_account_list(
        db=db,
    )


@mt5_account_controller.get("/get_one")
async def mt5_account_get_one(
    state: RequestState = Depends(RequestDepends.state),
    query: Mt5AccountQuery = Depends(Mt5AccountQuery.load_query),
    db: Session = Depends(PostgresConn.get_db),
) -> dict[str, Any]:
    return await mt5_account_service.mt5_account_get_one(
        db=db,
        query=query,
    )


@mt5_account_controller.post("/create")
async def mt5_account_create(
    body: Mt5AccountCreateBody,
    state: RequestState = Depends(RequestDepends.state),
    db: Session = Depends(PostgresConn.get_db),
) -> dict[str, Any]:
    return await mt5_account_service.mt5_account_create(
        db=db,
        body=body,
    )


@mt5_account_controller.post("/update/{user_id}")
async def mt5_account_update(
    user_id: int,
    body: Mt5AccountUpdateBody,
    state: RequestState = Depends(RequestDepends.state),
    db: Session = Depends(PostgresConn.get_db),
) -> dict[str, Any]:
    return await mt5_account_service.mt5_account_update(
        db=db,
        user_id=user_id,
        body=body,
    )
