from pydantic import BaseModel, Field
from typing import List
from app.postgres.entities.user_entity import UserType


class UserInfo(BaseModel):
    fullName: str = Field(..., min_length=3)
    isActive: int = Field(...)
    userType: UserType = Field(default=UserType.USER)


class AccountInfo(BaseModel):
    username: str = Field(..., min_length=5)
    password: str = Field(..., min_length=6)


class UserCreateBody(BaseModel):
    user: UserInfo = Field(...)
    account: AccountInfo = Field(...)
    roleIdList: List[int] = Field(...)


class UserUpdateBody(BaseModel):
    user: UserInfo = Field(...)
    account: AccountInfo | None = Field(default=None)
    roleIdList: List[int] | None = Field(default=None)
