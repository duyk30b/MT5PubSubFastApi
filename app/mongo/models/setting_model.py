from enum import StrEnum, unique
from typing import Any, ClassVar, NotRequired, Optional, Self, TypedDict

from pymongo import ASCENDING

from app.mongo.mongo_model import (
    MongoCreateSchema,
    MongoFilterSchema,
    MongoModel,
    MongoSortSchema,
    MongoUpdateSchema,
)


@unique
class SettingKey(StrEnum):
    UNKNOWN = "UNKNOWN"


class SettingModel(MongoModel):
    collection_name: ClassVar[str] = "setting"
    indexes: ClassVar[list[dict[str, Any]]] = [
        {"keys": [("key", ASCENDING)], "unique": True},
    ]
    key: SettingKey
    value: dict[str, Any] | str | int | bool


class SettingCreateDict(MongoCreateSchema):
    key: SettingKey
    value: dict[str, Any] | str | int | bool


class SettingUpdateDict(MongoUpdateSchema):
    key: NotRequired[SettingKey]
    value: dict[str, Any] | str | int | bool


class SettingFilterDict(MongoFilterSchema):
    key: SettingKey


class SettingSortDict(MongoSortSchema):
    key: Optional[int]  # 1 for ascending, -1 for descending
