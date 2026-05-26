from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.api_setting.setting_request import SettingUpsertBody
from app.api.api_setting.setting_service import SettingService
from app.depends.request_depends import RequestDepends, RequestState
from app.postgres.postgres_connection import PostgresConnection

setting_controller = APIRouter(prefix="/setting", tags=["Setting"])
setting_service = SettingService()


@setting_controller.get("/list")
async def setting_list(
    state: RequestState = Depends(RequestDepends.state),
    db: AsyncSession = Depends(PostgresConnection.get_db),
) -> dict[str, list[Any]]:
    data = await setting_service.setting_list(db=db)
    return data


@setting_controller.post("/upsert")
async def setting_upsert(
    body: SettingUpsertBody,
    db: AsyncSession = Depends(PostgresConnection.get_db),
) -> dict[str, Any]:
    data = await setting_service.setting_upsert(body=body, db=db)
    return data


@setting_controller.post("/destroy/{setting_id}")
async def setting_destroy(
    setting_id: int, db: AsyncSession = Depends(PostgresConnection.get_db)
) -> dict[str, Any]:
    data = await setting_service.setting_destroy(setting_id=setting_id, db=db)
    return data
