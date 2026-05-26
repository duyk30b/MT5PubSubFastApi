from typing import Any
from pprint import pprint

from app.api.api_setting.setting_request import SettingCreateBody, SettingUpdateBody
from app.mongo.models.setting_model import SettingCreateSchema, SettingKey
from app.mongo.repositories.setting_repository import setting_repository


class SettingService:
    def __init__(self):
        pass

    async def setting_list(self) -> dict[str, Any]:
        result = await setting_repository.find_many()
        return {"settingList": [setting.to_response() for setting in result]}

    async def setting_upsert(
        self, setting_key: SettingKey, body: SettingUpdateBody
    ) -> dict[str, Any]:
        setting = await setting_repository.upsert_one(
            filter={"key": setting_key},
            data={"key": setting_key, "value": body.value},
        )
        return {"setting": setting.to_response() if setting else None}

    async def setting_destroy(
        self,
        setting_id: str,
    ) -> dict[str, Any]:
        deleted_count = await setting_repository.delete(setting_id)
        return {"settingId": setting_id, "deletedCount": deleted_count}
