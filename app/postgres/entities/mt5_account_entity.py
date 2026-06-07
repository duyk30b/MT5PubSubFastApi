from enum import IntEnum, unique
from typing import Literal, NotRequired, Optional, Required

from sqlalchemy import BigInteger, Float, Integer, String
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
    copyMultiplier: float
    copyMasterLogin: int
    description: str


class MT5AccountEntity(PostgresEntity[MT5AccountDict, MT5AccountExcludeField]):
    __tablename__ = "MT5Account"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    accountType: Mapped[int] = mapped_column(Integer, default=MT5AccountType.NORMAL)
    accountLogin: Mapped[int] = mapped_column(BigInteger, default=0)
    accountName: Mapped[str] = mapped_column(String(50))
    accountServer: Mapped[str] = mapped_column(String(100))
    accountPassword: Mapped[str] = mapped_column(String(50))
    copyMultiplier: Mapped[float] = mapped_column(Float, default=1)
    copyMasterLogin: Mapped[int] = mapped_column(BigInteger, default=0)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


class MT5AccountCreateDict(PostgresCreateDict):
    accountType: Required[MT5AccountType]
    accountLogin: Required[int]
    accountName: Required[str]
    accountServer: Required[str]
    accountPassword: Required[str]
    copyMultiplier: Required[float]
    copyMasterLogin: Required[int]
    description: Required[str]


class MT5AccountUpdateDict(PostgresUpdateDict):
    accountType: NotRequired[MT5AccountType]
    accountLogin: NotRequired[int]
    accountName: NotRequired[str]
    accountServer: NotRequired[str]
    accountPassword: NotRequired[str]
    copyMultiplier: NotRequired[float]
    copyMasterLogin: NotRequired[int]
    description: NotRequired[str]


class MT5AccountFilterDict(PostgresFilterDict):
    accountType: NotRequired[MT5AccountType | None]
    accountLogin: NotRequired[int | None]
    accountName: NotRequired[str | None]
    accountServer: NotRequired[str | None]
    accountPassword: NotRequired[str | None]
    copyMultiplier: NotRequired[float | None]
    copyMasterLogin: NotRequired[int | None]
    description: NotRequired[str | None]


class MT5AccountSortDict(PostgresSortDict):
    accountType: NotRequired[int]
    accountLogin: NotRequired[int]
    accountName: NotRequired[int]
    accountServer: NotRequired[int]
    accountPassword: NotRequired[int]
    copyMultiplier: NotRequired[int]
    copyMasterLogin: NotRequired[int]
    description: NotRequired[int]


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
            copyMultiplier=1.0,
            copyMasterLogin=0,
            description="",
        )
