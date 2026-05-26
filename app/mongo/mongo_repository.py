from pprint import pprint
from pydoc import doc
from typing import Any, Dict, Optional, Type, TypeVar, Generic, List, TypedDict, Union

from pydantic import BaseModel
from sqlalchemy import Tuple, schema

from app.core.base_condition import FieldCondition
from app.mongo.mongo_condition import MongoCondition
from app.mongo.mongo_model import (
    MongoCreateSchema,
    MongoFilterSchema,
    MongoModel,
    MongoSortSchema,
    MongoUpdateSchema,
)
from app.mongo.mongo_connection import mongodb
from bson import ObjectId
from pymongo import UpdateOne, InsertOne, DeleteOne, ReturnDocument

M = TypeVar("M", bound=MongoModel)
C = TypeVar("C", bound=MongoCreateSchema)
U = TypeVar("U", bound=MongoUpdateSchema)
F = TypeVar("F", bound=MongoFilterSchema)
S = TypeVar("S", bound=MongoSortSchema)


class PaginationResult(Generic[M]):
    data: List[M]
    total: int
    page: int
    limit: int

    def __init__(self, **data: Any):
        self.__dict__.update(data)


class MongoRepository(Generic[M, C, U, F, S], MongoCondition):
    def __init__(self, model: Type[M]):
        self.model = model

    @property
    def collection(self):
        return mongodb.get_collection(self.model)

    def _to_filter(self, filter: Optional[F]) -> Dict[str, Any]:
        if not filter:
            return {}
        return self.get_filter_options(filter)  # type: ignore[arg-type]

    def _to_sort(self, sort: Optional[S]) -> List[tuple[str, int]]:
        if not sort:
            return []
        return self.get_sort_options(sort)  # type: ignore[arg-type]

    # ========================
    # Read
    # ========================
    async def pagination(
        self,
        filter: Optional[F] = None,
        page: int = 1,
        limit: int = 10,
        sort: Optional[S] = None,
    ) -> PaginationResult[M]:
        """
        Ví dụ:
            await repo.pagination(
                filter={"key": {"LIKE": "mql"}, "description": {"NOT_NULL": True}},
                page=1,
                limit=20,
                sort={"createdAt": "DESC"},
            )
        """
        mongo_filter = self._to_filter(filter)
        mongo_sort = self._to_sort(sort)

        skip = (page - 1) * limit
        cursor = self.collection.find(mongo_filter).skip(skip).limit(limit)
        if mongo_sort:
            cursor = cursor.sort(mongo_sort)  # type: ignore[arg-type]

        docs = await cursor.to_list(length=limit)

        total = await self.collection.count_documents(mongo_filter)
        return PaginationResult(
            data=[self.model.from_mongo(d) for d in docs],
            total=total,
            page=page,
            limit=limit,
        )

    async def find_many(
        self, filter: Optional[F] = None, limit: int | None = None
    ) -> List[M]:
        mongo_filter = self._to_filter(filter)

        cursor = self.collection.find(mongo_filter)
        if limit is not None:
            cursor = cursor.limit(limit)
        docs = [doc async for doc in cursor]
        return [self.model.from_mongo(d) for d in docs]

    async def find_one(self, filter: Optional[F] = None) -> M | None:
        mongo_filter = self._to_filter(filter)
        doc = await self.collection.find_one(mongo_filter)
        if not doc:
            return None
        return self.model.from_mongo(doc)

    async def find_one_by_id(self, id: str) -> M | None:
        doc = await self.collection.find_one({"_id": ObjectId(id)})
        if not doc:
            return None
        return self.model.from_mongo(doc)

    async def count(self, filter: Optional[F] = None) -> int:
        mongo_filter = self._to_filter(filter)
        return await self.collection.count_documents(mongo_filter)

    # ========================
    # Create
    # ========================
    async def insert_one(self, data: C) -> str:
        result = await self.collection.insert_one(data)
        return str(result.inserted_id)

    async def insert_many(self, data_list: List[C]) -> int:
        if not data_list:
            return 0

        data_dict_list = [data for data in data_list]
        result = await self.collection.insert_many(data_dict_list)

        return len(result.inserted_ids)

    # ========================
    # Update
    # ========================
    async def update_one(self, filter: F, data: U) -> M | None:
        mongo_filter = self._to_filter(filter)

        doc = await self.collection.find_one_and_update(
            mongo_filter,
            {"$set": data},
            upsert=False,
            return_document=ReturnDocument.AFTER,
        )

        if not doc:
            return None

        return self.model.from_mongo(doc)

    async def update_one_by_id(self, id: str, data: U) -> M | None:
        if not ObjectId.is_valid(id):
            raise ValueError("Invalid ObjectId")
        doc = await self.collection.find_one_and_update(
            {"_id": ObjectId(id)},
            {"$set": data},
            upsert=False,
            return_document=ReturnDocument.AFTER,
        )
        if not doc:
            return None

        return self.model.from_mongo(doc)

    async def upsert_one(self, filter: F, data: U) -> M | None:
        mongo_filter = self._to_filter(filter)
        doc = await self.collection.find_one_and_update(
            mongo_filter,
            {"$set": data},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        if not doc:
            return None
        return self.model.from_mongo(doc)

    async def bulk_update(self, updates: List[Dict[str, Any]]) -> int:
        # updates = [
        #     {"id": "...", "data": {...}},
        #     ...
        # ]

        if not updates:
            return 0

        operations: List[Any] = []
        for item in updates:
            id = item.get("id")
            data = item.get("data")
            if not id or not data:
                continue
            if not ObjectId.is_valid(id):
                continue
            operations.append(UpdateOne({"_id": ObjectId(id)}, {"$set": item["data"]}))

        if not operations:
            return 0

        result = await self.collection.bulk_write(operations)
        return result.modified_count

    # ========================
    # Delete
    # ========================
    async def delete(self, id: str) -> int:
        if not ObjectId.is_valid(id):
            raise ValueError("Invalid ObjectId")
        result = await self.collection.delete_one({"_id": ObjectId(id)})
        count = result.deleted_count
        return count
