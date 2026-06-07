from collections.abc import Iterable
from typing import Generic, NotRequired, TypedDict, TypeVar, cast

from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase


class PostgresDict(TypedDict):
    pass


R = TypeVar("R", bound=PostgresDict)
ExcludeField = TypeVar("ExcludeField", bound=str)


class PostgresEntity(DeclarativeBase, Generic[R, ExcludeField]):
    def to_response(
        self,
        exclude: Iterable[ExcludeField] | None = None,
    ) -> R:
        mapper = inspect(self).mapper
        excluded = set(exclude or [])
        return cast(
            R,
            {
                column.key: getattr(self, column.key)
                for column in mapper.column_attrs
                if column.key not in excluded
            },
        )


class PostgresCreateDict(TypedDict):
    pass


class PostgresUpdateDict(TypedDict):
    pass


class PostgresFilterDict(TypedDict):
    id: NotRequired[str]


class PostgresSortDict(TypedDict):
    id: NotRequired[int]  # 1 for ascending, -1 for descending
