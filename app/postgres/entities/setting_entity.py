from enum import StrEnum, unique
from typing import Literal, NotRequired, Required

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.postgres.postgres_entity import (
    PostgresCreateDict,
    PostgresDict,
    PostgresEntity,
    PostgresFilterDict,
    PostgresSortDict,
    PostgresUpdateDict,
)


@unique
class SettingKey(StrEnum):
    MT5_CONTAINER_FOLDER_PATH = "MT5_CONTAINER_FOLDER_PATH"


SettingExcludeField = Literal["id"]


class SettingDict(PostgresDict):
    id: int
    key: SettingKey
    value: str


class SettingEntity(PostgresEntity[SettingDict, SettingExcludeField]):
    __tablename__ = "Setting"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    key: Mapped[SettingKey] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    value: Mapped[str] = mapped_column(String(255), nullable=False)


class SettingCreateDict(PostgresCreateDict):
    key: Required[SettingKey]
    value: Required[str]


class SettingUpdateDict(PostgresUpdateDict):
    key: NotRequired[SettingKey]
    value: NotRequired[str]


class SettingFilterDict(PostgresFilterDict):
    key: NotRequired[SettingKey | None]
    value: NotRequired[str | None]


class SettingSortDict(PostgresSortDict):
    key: NotRequired[int]
    value: NotRequired[int]
