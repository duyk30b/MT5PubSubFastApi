from collections.abc import Iterable
from typing import Any, Generic, Optional, TypeVar, TypedDict

from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase

ExcludeFieldT = TypeVar("ExcludeFieldT", bound=str)


class PostgresEntity(DeclarativeBase, Generic[ExcludeFieldT]):
    def to_response(
        self,
        exclude: Iterable[ExcludeFieldT] | None = None,
    ) -> dict[str, Any]:
        mapper = inspect(self).mapper
        excluded = set(exclude or [])
        return {
            column.key: getattr(self, column.key)
            for column in mapper.column_attrs
            if column.key not in excluded
        }


class PostgresCreateSchema(TypedDict):
    pass


class PostgresUpdateSchema(TypedDict, total=False):
    pass


class PostgresFilterSchema(TypedDict, total=False):
    id: Optional[str]


class PostgresSortSchema(TypedDict, total=False):
    id: Optional[int]  # 1 for ascending, -1 for descending
