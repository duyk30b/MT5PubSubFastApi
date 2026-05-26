from typing import Any, ClassVar, Optional, Sequence, TypedDict

from bson import ObjectId
from pymongo import IndexModel


class MongoModel:
    collection_name: ClassVar[str]
    indexes: ClassVar[Sequence[IndexModel]] = []

    _id: ObjectId | None
    id: str | None

    def __init__(self, **data: Any):
        self.__dict__.update(data)
        self.id = str(self._id) if getattr(self, "_id", None) else None

    @classmethod
    def from_mongo(cls, doc: dict[str, Any]):
        return cls(**doc)

    def to_response(self):
        data = self.__dict__.copy()
        if self._id:
            data.pop("_id", None)

        return data


class MongoCreateSchema(TypedDict):
    pass


class MongoUpdateSchema(TypedDict, total=False):
    pass


class MongoFilterSchema(TypedDict, total=False):
    id: Optional[str]
    _id: Optional[str]


class MongoSortSchema(TypedDict, total=False):
    id: Optional[int]  # 1 for ascending, -1 for descending
    _id: Optional[int]
