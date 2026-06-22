from enum import IntEnum, unique
from typing import Literal, NotRequired, Optional, Required

from sqlalchemy import BigInteger, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_condition import FieldCondition, SortOrder
from app.postgres.postgres_entity import (
    PostgresCreateDict,
    PostgresDict,
    PostgresEntity,
    PostgresFilterDict,
    PostgresSortDict,
    PostgresUpdateDict,
)


@unique
class MT5AccountType(IntEnum):
    NORMAL = 0
    MASTER = 1
    FOLLOWER = 2


MT5AccountExcludeField = Literal["id"]


class MT5AccountDict(PostgresDict):
    id: int
    accountType: MT5AccountType
    accountLogin: int
    accountName: str
    accountServer: str
    accountPassword: str
    programName: str
    isOpening: int
    isCopying: int
    copyMultiplier: float
    copyMasterLogin: int
    description: str
    timeCorrectionSeconds: int


class MT5AccountEntity(PostgresEntity[MT5AccountDict, MT5AccountExcludeField]):
    __tablename__ = "MT5Account"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    accountType: Mapped[int] = mapped_column(Integer, default=MT5AccountType.NORMAL)
    accountLogin: Mapped[int] = mapped_column(BigInteger, default=0)
    accountName: Mapped[str] = mapped_column(String(50))
    accountServer: Mapped[str] = mapped_column(String(100))
    accountPassword: Mapped[str] = mapped_column(String(50))
    programName: Mapped[str] = mapped_column(String(50))
    isOpening: Mapped[int] = mapped_column(Integer, default=0)
    isCopying: Mapped[int] = mapped_column(Integer, default=0)
    copyMultiplier: Mapped[float] = mapped_column(Float, default=1)
    copyMasterLogin: Mapped[int] = mapped_column(BigInteger, default=0)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    timeCorrectionSeconds: Mapped[int] = mapped_column(Integer, default=0)


class MT5AccountCreateDict(PostgresCreateDict):
    accountType: Required[MT5AccountType]
    accountLogin: Required[int]
    accountName: Required[str]
    accountServer: Required[str]
    accountPassword: Required[str]
    programName: Required[str]
    isOpening: Required[int]
    isCopying: Required[int]
    copyMultiplier: Required[float]
    copyMasterLogin: Required[int]
    description: Required[str]
    timeCorrectionSeconds: Required[int]


class MT5AccountUpdateDict(PostgresUpdateDict):
    accountType: NotRequired[MT5AccountType]
    accountLogin: NotRequired[int]
    accountName: NotRequired[str]
    accountServer: NotRequired[str]
    accountPassword: NotRequired[str]
    programName: NotRequired[str]
    isOpening: NotRequired[int]
    isCopying: NotRequired[int]
    copyMultiplier: NotRequired[float]
    copyMasterLogin: NotRequired[int]
    description: NotRequired[str]
    timeCorrectionSeconds: NotRequired[int]


class MT5AccountFilterDict(PostgresFilterDict):
    accountType: NotRequired[MT5AccountType | FieldCondition[MT5AccountType] | None]
    accountLogin: NotRequired[int | FieldCondition[int] | None]
    accountName: NotRequired[str | FieldCondition[str] | None]
    accountServer: NotRequired[str | FieldCondition[str] | None]
    programName: NotRequired[str | FieldCondition[str] | None]
    isOpening: NotRequired[int | FieldCondition[int] | None]
    isCopying: NotRequired[int | FieldCondition[int] | None]
    copyMultiplier: NotRequired[float | FieldCondition[float] | None]
    copyMasterLogin: NotRequired[int | FieldCondition[int] | None]
    timeCorrectionSeconds: NotRequired[int | FieldCondition[int] | None]


class MT5AccountSortDict(PostgresSortDict):
    accountType: NotRequired[SortOrder]
    accountLogin: NotRequired[SortOrder]
    accountName: NotRequired[SortOrder]
    accountServer: NotRequired[SortOrder]
    programName: NotRequired[SortOrder]
    timeCorrectionSeconds: NotRequired[SortOrder]


class MT5AccountAction:
    @staticmethod
    def create_response_blank() -> MT5AccountDict:
        return MT5AccountDict(
            id=0,
            accountType=MT5AccountType.NORMAL,
            accountLogin=0,
            accountName="",
            accountServer="",
            accountPassword="",
            programName="",
            isOpening=0,
            isCopying=0,
            copyMultiplier=1.0,
            copyMasterLogin=0,
            description="",
            timeCorrectionSeconds=0,
        )
