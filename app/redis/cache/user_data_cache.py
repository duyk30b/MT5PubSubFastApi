import json
from typing import TypedDict

from app.redis.redis_base import RedisBase


class UserCached(TypedDict):
    id: int
    userType: int
    isActive: int


def _key_user(userId: int) -> str:
    return f"user:{userId}:data"


class UserDataCache(RedisBase):
    def __init__(self) -> None:
        super().__init__()

    async def set_user(self, user: UserCached) -> None:
        await self._set(_key_user(user["id"]), json.dumps(user, ensure_ascii=False))

    async def get_user(self, userId: int) -> UserCached | None:
        raw = await self._get(_key_user(userId))
        if raw is None:
            return None
        return json.loads(raw)

    async def delete_user(self, userId: int) -> None:
        await self._delete(_key_user(userId))

    async def warm_up(self, users: list[UserCached]) -> None:
        if not users:
            return
        async with self._pipeline() as pipe:
            for u in users:
                pipe.set(_key_user(u["id"]), json.dumps(u, ensure_ascii=False))
            await pipe.execute()


userDataCache = UserDataCache()
