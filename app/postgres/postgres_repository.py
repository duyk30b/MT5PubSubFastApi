from typing import Any, Generic, List, Optional, Type, TypeVar, cast

from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import InstrumentedAttribute

from app.postgres.postgres_condition import PostgresCondition
from app.postgres.postgres_entity import (
    PostgresCreateDict,
    PostgresEntity,
    PostgresFilterDict,
    PostgresSortDict,
    PostgresUpdateDict,
)

M = TypeVar("M", bound=PostgresEntity[Any, Any])
C = TypeVar("C", bound=PostgresCreateDict)
U = TypeVar("U", bound=PostgresUpdateDict)
F = TypeVar("F", bound=PostgresFilterDict)
S = TypeVar("S", bound=PostgresSortDict)


class PaginationResult(Generic[M]):
    data: List[M]
    total: int
    page: int
    limit: int

    def __init__(self, **data: Any):
        self.__dict__.update(data)


class PostgresRepository(Generic[M, C, U, F, S], PostgresCondition):
    def __init__(self, model: Type[M]):
        self.model = model

    def _to_filter(self, filter: Optional[F]) -> List[Any]:
        if not filter:
            return []
        return self.get_filter_clauses(self.model, filter)  # type: ignore[arg-type]

    def _to_sort(self, sort: Optional[S]) -> List[Any]:
        if not sort:
            return []
        return self.get_sort_clauses(self.model, sort)  # type: ignore[arg-type]

    # ========================
    # Read
    # ========================
    async def pagination(
        self,
        db: AsyncSession,
        filter: Optional[F] = None,
        page: int = 1,
        limit: int = 10,
        sort: Optional[S] = None,
    ) -> PaginationResult[M]:
        clauses = self._to_filter(filter)
        order = self._to_sort(sort)

        query = select(self.model)
        if clauses:
            query = query.where(*clauses)
        if order:
            query = query.order_by(*order)

        total_query = select(func.count()).select_from(self.model)
        if clauses:
            total_query = total_query.where(*clauses)

        total_result = await db.execute(total_query)
        total = total_result.scalar_one()

        data_query = query.offset((page - 1) * limit).limit(limit)
        data_result = await db.execute(data_query)
        data = list(data_result.scalars().all())

        return PaginationResult(data=data, total=total, page=page, limit=limit)

    async def find_many(
        self,
        db: AsyncSession,
        filter: Optional[F] = None,
        limit: Optional[int] = None,
        sort: Optional[S] = None,
    ) -> List[M]:
        clauses = self._to_filter(filter)
        order = self._to_sort(sort)

        query = select(self.model)
        if clauses:
            query = query.where(*clauses)
        if order:
            query = query.order_by(*order)
        if limit is not None:
            query = query.limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def find_one(self, db: AsyncSession, filter: Optional[F] = None) -> M | None:
        clauses = self._to_filter(filter)
        query = select(self.model)
        if clauses:
            query = query.where(*clauses)
        result = await db.execute(query.limit(1))
        return result.scalars().first()

    # ========================
    # Create
    # ========================
    async def insert_one(self, db: AsyncSession, data: C, commit: bool = True) -> M:
        obj = self.model(**data)
        db.add(obj)
        if commit:
            await db.commit()
            await db.refresh(obj)
        return obj

    async def insert_many(
        self, db: AsyncSession, data_list: List[C], commit: bool = True
    ) -> int:
        if not data_list:
            return 0
        objs = [self.model(**data) for data in data_list]
        db.add_all(objs)
        if commit:
            await db.commit()
        return len(objs)

    # ========================
    # Update
    # ========================
    async def update(
        self, db: AsyncSession, filter: F, data: U, commit: bool = True
    ) -> int:
        if not data:
            return 0

        stmt = update(self.model).values(**data)

        clauses = self._to_filter(filter)
        if clauses:
            stmt = stmt.where(*clauses)

        result = await db.execute(stmt)
        if commit:
            await db.commit()

        rowcount = cast(CursorResult[Any], result).rowcount
        return rowcount or 0

    async def bulk_update(
        self,
        db: AsyncSession,
        data_list: list[dict[str, Any]],
        commit: bool = True,
    ) -> None:
        """
        rows = [
            {
                "id": 1,
                "name": "A"
            },
            {
                "id": 2,
                "name": "B"
            }
        ]
        """
        await db.run_sync(
            lambda sync_session: sync_session.bulk_update_mappings(
                self.model.__mapper__,
                data_list,
            )
        )

        if commit:
            await db.commit()

    async def update_conflict(
        self,
        db: AsyncSession,
        data: dict[str, Any],
        conflict_columns: list[str],
    ) -> None:
        stmt = insert(self.model).values(**data)

        update_values = {k: v for k, v in data.items() if k not in conflict_columns}

        stmt = stmt.on_conflict_do_update(
            index_elements=conflict_columns,
            set_=update_values,
        )

        await db.execute(stmt)

        await db.commit()

    # ========================
    # Delete
    # ========================
    async def delete(
        self,
        db: AsyncSession,
        filter: F,
    ) -> int:
        clauses = self._to_filter(filter)
        stmt = delete(self.model).where(*clauses)

        result = await db.execute(stmt)

        await db.commit()

        rowcount = cast(CursorResult[Any], result).rowcount
        return rowcount or 0

    async def exists(
        self,
        db: AsyncSession,
        filter: F,
    ) -> bool:
        clauses = self._to_filter(filter)
        stmt = select(select(self.model).where(*clauses).exists())
        result = await db.scalar(stmt)
        return bool(result)

    async def count(self, db: AsyncSession, filter: F) -> int:
        clauses = self._to_filter(filter)
        query = select(func.count()).select_from(self.model).where(*clauses)
        result = await db.execute(query)
        return result.scalar_one()

    async def find_one_by_id(self, db: AsyncSession, id: int) -> M | None:
        return await db.get(self.model, id)

    async def find_many_by(
        self,
        db: AsyncSession,
        values: list[int],
        column: InstrumentedAttribute[Any],
    ) -> list[M]:
        if not values:
            return []

        stmt = select(self.model).where(column.in_(values))

        result = await db.execute(stmt)

        return list(result.scalars().all())

    async def update_one_by_id(
        self,
        db: AsyncSession,
        id: int,
        data: U,
        commit: bool = True,
    ) -> M | None:
        if not data:
            return await self.find_one_by_id(db, id)

        model_id = getattr(self.model, "id", None)
        if model_id is None:
            raise ValueError(f"Model '{self.model.__name__}' does not have 'id' column")

        stmt = (
            update(self.model)
            .where(model_id == id)
            .values(**data)
            .execution_options(synchronize_session="fetch")
        )

        result = await db.execute(stmt)

        if commit:
            await db.commit()

        rowcount = cast(CursorResult[Any], result).rowcount
        if rowcount and rowcount > 0:
            return await self.find_one_by_id(db, id)
        return None

    async def delete_by_id(self, db: AsyncSession, id: int) -> bool:
        model_id = getattr(self.model, "id", None)
        if model_id is None:
            raise ValueError(f"Model '{self.model.__name__}' does not have 'id' column")

        stmt = delete(self.model).where(model_id == id)

        result = await db.execute(stmt)

        await db.commit()

        rowcount = cast(CursorResult[Any], result).rowcount
        return bool(rowcount and rowcount > 0)

    async def upsert_one(self, db: AsyncSession, filter: F, data: C | U) -> M:
        obj = await self.find_one(db, filter)
        if obj:
            for k, v in data.items():  # type: ignore[attr-defined]
                setattr(obj, k, v)
            await db.commit()
            await db.refresh(obj)
            return obj
        else:
            new_obj = self.model(**data)
            db.add(new_obj)
            await db.commit()
            await db.refresh(new_obj)
            return new_obj
