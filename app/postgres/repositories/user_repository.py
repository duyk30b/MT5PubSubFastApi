# app/repositories/user_repository.py
from sqlalchemy.orm import Session

from app.postgres.postgres_repository import PostgresRepository
from app.postgres.entities.user_entity import (
    UserCreateSchema,
    UserEntity,
    UserUpdateSchema,
    UserFilterSchema,
    UserSortSchema,
)


class UserRepository(
    PostgresRepository[
        UserEntity, UserCreateSchema, UserUpdateSchema, UserFilterSchema, UserSortSchema
    ]
):
    def __init__(self):
        super().__init__(UserEntity)


user_repository = UserRepository()
