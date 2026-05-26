from pydantic import BaseModel, Field

from app.core.camel_model import CamelModel
from app.mongo.models.setting_model import SettingKey


class SettingCreateBody(CamelModel):
    key: SettingKey = Field(...)
    value: str = Field(...)


class SettingUpdateBody(CamelModel):
    value: str = Field(...)
