import logging
from collections.abc import Generator

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from .postgres_config import postgres_settings

logger = logging.getLogger(__name__)


class PostgresConnection:
    def __init__(self) -> None:
        self.engine: Engine | None = None
        self.SessionLocal: sessionmaker[Session] | None = None

    async def connect(self) -> None:
        self.engine = create_engine(
            postgres_settings.sqlalchemy_database_uri, pool_pre_ping=True
        )
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

        try:
            # Force an immediate DB round-trip so startup fails fast on bad config.
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.debug(
                f"Successfully connected to PostgreSQL: {postgres_settings.sqlalchemy_database_uri}"
            )
        except Exception as exc:
            await self.close()
            logger.error(
                f"Failed to connect PostgreSQL: {postgres_settings.sqlalchemy_database_uri}: {exc}"
            )
            raise RuntimeError(
                f"Failed to connect PostgreSQL: {postgres_settings.sqlalchemy_database_uri}: {exc}"
            )

    async def close(self) -> None:
        if self.engine is not None:
            self.engine.dispose()
        self.engine = None
        self.SessionLocal = None

    def get_db(self) -> Generator[Session, None, None]:
        if self.SessionLocal is None:
            raise RuntimeError(
                "PostgreSQL session factory is not initialized. Call connect() first."
            )
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()


PostgresConn = PostgresConnection()
