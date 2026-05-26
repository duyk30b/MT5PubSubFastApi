import asyncio
import logging
from typing import Any, List, Type

from pymongo import AsyncMongoClient
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.database import AsyncDatabase

from app.mongo.models.setting_model import SettingModel
from app.mongo.mongo_config import mongo_settings
from app.mongo.mongo_model import MongoModel

logger = logging.getLogger(__name__)


class MongoDBConnectionBase:
    def __init__(self) -> None:
        self.client: None | AsyncMongoClient[Any] = None

        self.collections: List[Type[MongoModel]] = [
            SettingModel,
        ]

    async def connect(self, retries: int = 3, delay: int = 5) -> None:
        if self.client is not None:
            logger.warning("MongoDB client is already connected.")
            return

        for attempt in range(1, retries + 1):
            try:
                self.client = AsyncMongoClient(
                    mongo_settings.mongo_uri,
                    serverSelectionTimeoutMS=5000,  # timeout tìm primary
                    connectTimeoutMS=5000,  # timeout khi mở TCP
                    socketTimeoutMS=30000,  # timeout query
                    maxPoolSize=100,  # số connection tối đa
                    minPoolSize=5,  # giữ sẵn connection
                    maxIdleTimeMS=60000,  # tự đóng connection nhàn rỗi
                    retryWrites=True,  # retry insert/update
                    retryReads=True,  # retry read
                    heartbeatFrequencyMS=10000,  # kiểm tra primary còn sống
                )
                await self.client.admin.command("ping")
                logger.debug(
                    f"Successfully connected to MongoDB: {mongo_settings.mongo_uri}"
                )
                return

            except Exception as exc:
                await self.close()
                if attempt < retries:
                    logger.warning(
                        f"MongoDB connection Failed Attempt {attempt}/{retries}: {exc}"
                    )
                    await asyncio.sleep(delay)
                else:
                    raise RuntimeError(
                        f"Failed to connect MongoDB after {retries} attempts: {exc}"
                    )

    async def initialize(self) -> None:
        await self.connect()
        await self.create_indexes()

    async def close(self) -> None:
        if self.client:
            await self.client.close()
            self.client = None

    def get_database(self) -> AsyncDatabase[Any]:
        if self.client is None:
            raise RuntimeError("MongoDB client is not connected. Call connect() first.")
        return self.client[mongo_settings.MONGO_DATABASE_NAME]

    def get_collection(self, model_cls: Type[MongoModel]) -> AsyncCollection[Any]:
        if not model_cls.collection_name:
            raise ValueError(f"{model_cls.__name__} collection_name is empty")
        db = self.get_database()
        return db[model_cls.collection_name]

    async def health_check(self) -> bool:
        try:
            if self.client is None:
                raise RuntimeError(
                    "MongoDB client is not connected. Call connect() first."
                )
            await self.client.admin.command("ping")
            return True
        except Exception:
            return False

    async def create_indexes(self):
        db = self.get_database()

        for model in self.collections:
            if not getattr(model, "indexes", None):
                continue

            collection = db[model.collection_name]
            await collection.create_indexes(model.indexes)


MongoDBConnection = MongoDBConnectionBase()
