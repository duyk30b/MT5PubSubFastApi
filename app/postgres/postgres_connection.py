import asyncio
import logging
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .postgres_config import postgres_settings

logger = logging.getLogger(__name__)


class PostgresConnectionBase:
    def __init__(self) -> None:
        self.engine: AsyncEngine | None = None
        self.SessionLocal: async_sessionmaker[AsyncSession] | None = None

    async def connect(self, retries: int = 3, delay: int = 5) -> None:
        uri = postgres_settings.sqlalchemy_uri_app
        if self.engine is not None:
            logger.warning("PostgreSQL already connected !")
            return

        for attempt in range(1, retries + 1):
            try:
                self.engine = create_async_engine(
                    uri,
                    # connect_args=postgres_settings.sqlalchemy_query_args,
                    pool_pre_ping=True,  # kiểm tra connection còn sống
                    pool_size=20,  # số connection thường trực
                    max_overflow=10,  # số connection được mở thêm
                    pool_recycle=3600,  # tránh connection timeout
                    echo=False,
                )
                self.SessionLocal = async_sessionmaker(
                    bind=self.engine,
                    autocommit=False,
                    autoflush=False,
                )
                async with self.engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))
                logger.debug(f"Successfully connected to PostgreSQL: {uri}")
                return

            except Exception as exc:
                await self.close()
                if attempt < retries:
                    logger.warning(
                        f"PostgreSQL connection Failed Attempt {attempt}/{retries}: {exc}"
                    )
                    await asyncio.sleep(delay)
                else:
                    raise RuntimeError(
                        f"Failed to connect to PostgreSQL after {retries} attempts: {exc}"
                    )

    async def close(self) -> None:
        if self.engine is not None:
            await self.engine.dispose()
        self.engine = None
        self.SessionLocal = None

    async def get_db(self) -> AsyncGenerator[AsyncSession, None]:
        if self.SessionLocal is None:
            raise RuntimeError(
                "PostgreSQL session factory is not initialized. Call connect() first."
            )
        db = self.SessionLocal()
        try:
            yield db
        finally:
            await db.close()


PostgresConnection = PostgresConnectionBase()
