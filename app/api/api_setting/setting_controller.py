from math import e
from typing import Any

from fastapi import APIRouter

from app.api.api_setting.setting_service import SettingService
from app.api.api_setting.setting_request import SettingCreateBody, SettingUpdateBody
from app.mongo.models.setting_model import SettingKey

setting_controller = APIRouter(prefix="/setting", tags=["Setting"])
setting_service = SettingService()


@setting_controller.get("/list")
async def setting_list() -> dict[str, list[Any]]:
    data = await setting_service.setting_list()
    return data


@setting_controller.post("/upsert/{setting_key}")
async def setting_upsert(
    setting_key: SettingKey, body: SettingUpdateBody
) -> dict[str, Any]:
    data = await setting_service.setting_upsert(setting_key=setting_key, body=body)
    return data


@setting_controller.post("/destroy/{setting_id}")
async def setting_destroy(setting_id: str) -> dict[str, Any]:
    data = await setting_service.setting_destroy(setting_id=setting_id)
    return data
