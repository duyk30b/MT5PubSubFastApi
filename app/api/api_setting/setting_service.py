from typing import Any

from sqlalchemy.orm import Session

from app.api.api_setting.setting_request import SettingUpsertBody
from app.postgres.entities.setting_entity import SettingKey
from app.postgres.repositories.setting_repository import setting_repository


class SettingService:
    def __init__(self):
        pass

    async def setting_list(self, db: Session) -> dict[str, Any]:
        result = setting_repository.find_many(db=db)
        settingList = [setting.to_response() for setting in result]
        return {"settingList": settingList}

    async def setting_upsert(
        self, db: Session, body: SettingUpsertBody
    ) -> dict[str, Any]:
        key = SettingKey(str(body.key))
        setting = setting_repository.upsert_one(
            db=db,
            filter={"key": key},
            data={"key": key, "value": body.value},
        )
        return {"setting": setting.to_response() if setting else None}

    async def setting_destroy(
        self,
        db: Session,
        setting_id: str,
    ) -> dict[str, Any]:
        deleted_count = setting_repository.delete_one(db=db, filter={"id": setting_id})
        return {"settingId": setting_id, "deletedCount": deleted_count}
