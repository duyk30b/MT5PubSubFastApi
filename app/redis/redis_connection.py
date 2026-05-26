import logging

from redis.asyncio import Redis, ConnectionPool
from app.redis.redis_config import redis_settings

logger = logging.getLogger(__name__)


class RedisConnection:
    def __init__(self) -> None:
        self._pool: ConnectionPool | None = None
        self.client: Redis | None = None

    async def connect(self) -> None:
        self._pool = ConnectionPool(
            host=redis_settings.REDIS_HOST,
            port=redis_settings.REDIS_PORT,
            db=redis_settings.REDIS_DB,
            password=redis_settings.REDIS_PASSWORD,
            decode_responses=True,
            max_connections=20,
        )
        self.client = Redis(connection_pool=self._pool)
        try:
            await self.client.ping()  # type: ignore[misc]  # Kiểm tra kết nối
            logger.debug(
                f"Successfully connected to Redis: "
                f"{redis_settings.REDIS_HOST}:{redis_settings.REDIS_PORT}"
            )
        except Exception as exc:
            await self.close()
            logger.error(
                f"Failed to connect Redis: "
                f"{redis_settings.REDIS_HOST}:{redis_settings.REDIS_PORT}: {exc}"
            )
            raise RuntimeError(
                f"Failed to connect Redis: "
                f"{redis_settings.REDIS_HOST}:{redis_settings.REDIS_PORT}: {exc}"
            )

    async def close(self) -> None:
        if self.client:
            await self.client.aclose()
        if self._pool:
            await self._pool.aclose()

    def get_client(self) -> Redis:
        if self.client is None:
            raise RuntimeError("Redis client is not initialized. Call connect() first.")
        return self.client


redisConnection = RedisConnection()
