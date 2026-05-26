from redis.exceptions import ResponseError

from app.redis.redis_base import RedisBase


def _key_user_login(userId: int) -> str:
    return f"user:{userId}:login"


class UserLoginCache(RedisBase):
    def __init__(self) -> None:
        super().__init__()

    async def login(self, userId: int, clientId: str, loginTime: float) -> None:
        key = _key_user_login(userId)
        try:
            await self._hash_set(key, {f"{clientId}": loginTime})
        except ResponseError:
            await self._delete(key)
            await self._hash_set(key, {f"{clientId}": loginTime})

    async def logout(self, userId: int, clientId: str, loginTime: float) -> None:
        await self._hash_delete(_key_user_login(userId), f"{clientId}")

    async def logout_all(self, userId: int) -> None:
        await self._delete(_key_user_login(userId))

    async def check_client(self, userId: int, clientId: str, loginTime: float) -> bool:
        # return await self._hash_exists(_key_user_login(userId), f"{clientId}")
        return await self._hash_get(_key_user_login(userId), f"{clientId}") == str(
            loginTime
        )


userLoginCache = UserLoginCache()
