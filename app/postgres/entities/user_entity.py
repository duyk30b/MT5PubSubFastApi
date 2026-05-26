from enum import IntEnum, unique
from typing import Literal, Optional

from sqlalchemy import BigInteger, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.postgres.postgres_entity import (
    PostgresCreateSchema,
    PostgresEntity,
    PostgresFilterSchema,
    PostgresSortSchema,
    PostgresUpdateSchema,
)


@unique
class UserType(IntEnum):
    ROOT = 0
    ADMIN = 1
    USER = 2


UserResponseField = Literal[
    "id",
    "fullName",
    "username",
    "passwordHash",
    "userType",
    "isActive",
    "createdAt",
    "updatedAt",
]


class UserEntity(PostgresEntity[UserResponseField]):
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


class UserCreateSchema(PostgresCreateSchema):
    fullName: str
    username: str
    passwordHash: str
    userType: UserType
    isActive: int
    createdAt: int
    updatedAt: int


class UserUpdateSchema(PostgresUpdateSchema, total=False):
    fullName: str
    username: str
    passwordHash: str
    userType: UserType
    isActive: int
    createdAt: int
    updatedAt: int


class UserFilterSchema(PostgresFilterSchema, total=False):
    fullName: Optional[str]
    username: Optional[str]
    userType: Optional[UserType]


class UserSortSchema(PostgresSortSchema, total=False):
    userType: Optional[int]  # 1 for ascending, -1 for descending
    username: Optional[int]
    isActive: Optional[int]
