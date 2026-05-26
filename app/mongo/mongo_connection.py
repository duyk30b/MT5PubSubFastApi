import logging
from typing import Any, List, Optional, Type

from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from app.mongo.models.setting_model import SettingModel
from app.mongo.mongo_model import MongoModel
from app.mongo.mongo_config import mongo_settings

logging.getLogger("pymongo").setLevel(logging.INFO)
logger = logging.getLogger(__name__)


class MongoDB:
    def __init__(self) -> None:
        self.client: None | AsyncMongoClient[Any] = None

        self.collections: List[Type[MongoModel]] = [
            SettingModel,
        ]

    async def connect(self) -> None:
        self.client = AsyncMongoClient(
            mongo_settings.mongo_uri,
            serverSelectionTimeoutMS=5000,
        )
        try:
            await self.client.admin.command("ping")
            logger.debug(
                f"Successfully connected to MongoDB: {mongo_settings.mongo_uri}"
            )
        except Exception as exc:
            await self.close()
            logger.error(
                f"Failed to connect MongoDB: {mongo_settings.mongo_uri}: {exc}"
            )
            raise RuntimeError(
                f"Failed to connect MongoDB: {mongo_settings.mongo_uri}: {exc}"
            )

    async def close(self) -> None:
        if self.client:
            await self.client.close()
            self.client = None

    def get_database(self) -> AsyncDatabase[Any]:
        if self.client is None:
            raise RuntimeError("MongoDB client is not connected. Call connect() first.")
        return self.client[mongo_settings.MONGO_DATABASE_NAME]

    def get_collection(self, model_cls: Type[MongoModel]):
        db = self.get_database()
        return db[model_cls.collection_name]


mongodb = MongoDB()
