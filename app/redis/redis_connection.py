import asyncio
import logging

from redis.asyncio import ConnectionPool, Redis

from app.redis.redis_config import redis_settings

logger = logging.getLogger(__name__)


class RedisConnectionBase:
    def __init__(self) -> None:
        self._pool: ConnectionPool | None = None
        self.client: Redis | None = None

    async def connect(self, retries: int = 20, delay: int = 5) -> None:
        if self.client is not None:
            logger.warning("Redis already connected !")
            return

        for attempt in range(1, retries + 1):
            try:
                self._pool = ConnectionPool(
                    host=redis_settings.REDIS_HOST,
                    port=redis_settings.REDIS_PORT,
                    db=redis_settings.REDIS_DB,
                    password=redis_settings.REDIS_PASSWORD,
                    protocol=redis_settings.REDIS_PROTOCOL,
                    decode_responses=True,  # Giải mã dữ liệu trả về từ Redis thành chuỗi (string) thay vì bytes
                    max_connections=20,  # Số lượng kết nối tối đa trong pool
                    socket_connect_timeout=5,  # Timeout khi mở kết nối TCP
                    socket_timeout=5,  # Timeout cho các lệnh Redis
                    socket_keepalive=True,  # Giữ kết nối TCP sống
                    health_check_interval=30,  # Kiểm tra kết nối cứ 30 giây
                )
                self.client = Redis(connection_pool=self._pool)

                await self.client.ping()  # type: ignore[misc]  # Kiểm tra kết nối
                logger.debug(
                    f"Successfully connected to Redis: "
                    f"{redis_settings.REDIS_HOST}:{redis_settings.REDIS_PORT}"
                )
                return

            except Exception as exc:
                await self.close()
                if attempt < retries:
                    logger.warning(
                        f"Redis connection Failed Attempt {attempt}/{retries}: {exc}"
                    )
                    await asyncio.sleep(delay)
                else:
                    raise RuntimeError(
                        f"Failed to connect to Redis after {retries} attempts: {exc}"
                    )

    async def close(self) -> None:
        if self.client:
            await self.client.aclose()
            self.client = None
        if self._pool:
            await self._pool.aclose()
            self._pool = None

    def get_client(self) -> Redis:
        if self.client is None:
            raise RuntimeError("Redis client is not initialized. Call connect() first.")
        return self.client


RedisConnection = RedisConnectionBase()
