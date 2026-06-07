from pydantic import BaseModel, Field

from app.postgres.entities.setting_entity import SettingKey


class SettingUpsertBody(BaseModel):
    key: SettingKey = Field(...)
    value: str = Field(...)
