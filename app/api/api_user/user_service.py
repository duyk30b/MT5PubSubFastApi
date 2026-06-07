import logging
import time
from typing import Any

from sqlalchemy.orm import Session

from app.api.api_user.user_request import UserCreateBody, UserUpdateBody
from app.core.exception import BusinessException
from app.core.security import hash_password
from app.postgres.entities.user_entity import (
    UserCreateDict,
    UserUpdateDict,
)
from app.postgres.repositories.user_repository import user_repository
from app.redis.cache.user_data_cache import userDataCache
from app.redis.cache.user_login_cache import userLoginCache

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self):
        pass

    async def user_pagination(
        self,
        db: Session,
        page: int,
        limit: int,
    ) -> dict[str, Any]:
        result = user_repository.pagination(db, page=page, limit=limit)
        userList = [u.to_response(exclude=["passwordHash"]) for u in result.data]

        return {
            "userList": userList,
            "total": result.total,
            "limit": result.limit,
            "page": result.page,
        }

    async def user_list(
        self,
        db: Session,
    ) -> dict[str, Any]:
        users = user_repository.find_many(db)
        userList = [u.to_response(exclude=["passwordHash"]) for u in users]
        return {"userList": userList}

    async def user_detail(
        self,
        db: Session,
        user_id: int,
    ) -> dict[str, Any]:
        user = user_repository.find_one_by_id(db, user_id)
        if not user:
            raise BusinessException("User not found")
        return {"user": user.to_response(exclude=["passwordHash"])}

    async def user_create(
        self,
        db: Session,
        body: UserCreateBody,
    ) -> dict[str, Any]:
        existed = user_repository.find_one(db, {"username": body.account.username})
        if existed:
            raise BusinessException("Username already exists")

        now = int(time.time() * 1000)
        user = user_repository.insert_one(
            db,
            UserCreateDict(
                fullName=body.user.fullName,
                username=body.account.username,
                passwordHash=hash_password(body.account.password),
                userType=body.user.userType,
                isActive=body.user.isActive,
                createdAt=now,
                updatedAt=now,
            ),
        )

        await userDataCache.set_user(
            {"id": user.id, "userType": user.userType, "isActive": user.isActive}
        )
        return {"user": user.to_response(exclude=["passwordHash"])}

    async def user_update(
        self,
        db: Session,
        user_id: int,
        body: UserUpdateBody,
    ) -> dict[str, Any]:
        update_data = UserUpdateDict(
            fullName=body.user.fullName,
            userType=body.user.userType,
            isActive=body.user.isActive,
            updatedAt=int(time.time() * 1000),
        )
        if body.account:
            update_data["username"] = body.account.username
            update_data["passwordHash"] = hash_password(body.account.password)

        user = user_repository.update_one_by_id(db, user_id, update_data)
        if not user:
            raise BusinessException("User not found")

        await userDataCache.set_user(
            {"id": user.id, "userType": user.userType, "isActive": user.isActive}
        )
        return {"user": user.to_response(exclude=["passwordHash"])}

    async def user_destroy(self, db: Session, user_id: int) -> dict[str, Any]:
        user = user_repository.find_one_by_id(db, user_id)
        if not user:
            raise BusinessException("User not found")
        user_repository.delete_by_id(db, user_id)
        await userDataCache.delete_user(user_id)
        return {"success": True}

    async def user_force_logout(self, user_id: int) -> dict[str, Any]:
        await userLoginCache.logout_all(user_id)
        return {"message": f"Force-logged out user {user_id}"}
