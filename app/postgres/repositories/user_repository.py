# app/repositories/user_repository.py
from sqlalchemy.orm import Session

from app.postgres.entities.user_entity import (
    UserCreateDict,
    UserEntity,
    UserFilterDict,
    UserSortDict,
    UserUpdateDict,
)
from app.postgres.postgres_repository import PostgresRepository


class UserRepository(
    PostgresRepository[
        UserEntity, UserCreateDict, UserUpdateDict, UserFilterDict, UserSortDict
    ]
):
    def __init__(self):
        super().__init__(UserEntity)


user_repository = UserRepository()
