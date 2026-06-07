from enum import IntEnum, unique
from typing import Literal, NotRequired, Required

from sqlalchemy import BigInteger, Integer, String
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
class UserType(IntEnum):
    ROOT = 0
    ADMIN = 1
    USER = 2


UserExcludeField = Literal["passwordHash"]


class UserDict(PostgresDict):
    fullName: str
    username: str
    passwordHash: str
    userType: UserType
    isActive: int
    createdAt: int
    updatedAt: int


class UserEntity(PostgresEntity[UserDict, UserExcludeField]):
    __tablename__ = "User"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    fullName: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    passwordHash: Mapped[str] = mapped_column(String(255), nullable=False)
    userType: Mapped[int] = mapped_column(Integer, default=UserType.USER)
    isActive: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    createdAt: Mapped[int] = mapped_column(BigInteger, nullable=False)
    updatedAt: Mapped[int] = mapped_column(BigInteger, nullable=False)


class UserCreateDict(PostgresCreateDict):
    fullName: Required[str]
    username: Required[str]
    passwordHash: Required[str]
    userType: Required[UserType]
    isActive: Required[int]
    createdAt: Required[int]
    updatedAt: Required[int]


class UserUpdateDict(PostgresUpdateDict):
    fullName: NotRequired[str]
    username: NotRequired[str]
    passwordHash: NotRequired[str]
    userType: NotRequired[UserType]
    isActive: NotRequired[int]
    createdAt: NotRequired[int]
    updatedAt: NotRequired[int]


class UserFilterDict(PostgresFilterDict):
    fullName: NotRequired[str | None]
    username: NotRequired[str | None]
    userType: NotRequired[UserType | None]


class UserSortDict(PostgresSortDict):
    userType: NotRequired[int]  # 1 for ascending, -1 for descending
    username: NotRequired[int]
    isActive: NotRequired[int]
