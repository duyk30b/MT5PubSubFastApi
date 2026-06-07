from typing import Any, Generic, List, Optional, Type, TypeVar

from sqlalchemy.orm import Session

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
    def pagination(
        self,
        db: Session,
        filter: Optional[F] = None,
        page: int = 1,
        limit: int = 10,
        sort: Optional[S] = None,
    ) -> PaginationResult[M]:
        clauses = self._to_filter(filter)
        order = self._to_sort(sort)

        query = db.query(self.model)
        if clauses:
            query = query.filter(*clauses)
        if order:
            query = query.order_by(*order)

        total = query.count()
        data = query.offset((page - 1) * limit).limit(limit).all()

        return PaginationResult(data=data, total=total, page=page, limit=limit)

    def find_many(
        self,
        db: Session,
        filter: Optional[F] = None,
        limit: Optional[int] = None,
        sort: Optional[S] = None,
    ) -> List[M]:
        clauses = self._to_filter(filter)
        order = self._to_sort(sort)

        query = db.query(self.model)
        if clauses:
            query = query.filter(*clauses)
        if order:
            query = query.order_by(*order)
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    def find_one(self, db: Session, filter: Optional[F] = None) -> M | None:
        clauses = self._to_filter(filter)
        query = db.query(self.model)
        if clauses:
            query = query.filter(*clauses)
        return query.first()

    def find_one_by_id(self, db: Session, id: int) -> M | None:
        return db.get(self.model, id)

    def count(self, db: Session, filter: Optional[F] = None) -> int:
        clauses = self._to_filter(filter)
        query = db.query(self.model)
        if clauses:
            query = query.filter(*clauses)
        return query.count()

    # ========================
    # Create
    # ========================
    def insert_one(self, db: Session, data: C) -> M:
        obj = self.model(**data)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def insert_many(self, db: Session, data_list: List[C]) -> int:
        if not data_list:
            return 0
        objs = [self.model(**data) for data in data_list]
        db.add_all(objs)
        db.commit()
        return len(objs)

    # ========================
    # Update
    # ========================
    def update_one(self, db: Session, filter: F, data: U) -> M | None:
        obj = self.find_one(db, filter)
        if not obj:
            return None
        for k, v in data.items():  # type: ignore[attr-defined]
            setattr(obj, k, v)
        db.commit()
        db.refresh(obj)
        return obj

    def update_one_by_id(self, db: Session, id: int, data: U) -> M | None:
        obj = db.get(self.model, id)
        if not obj:
            return None
        for k, v in data.items():  # type: ignore[attr-defined]
            setattr(obj, k, v)
        db.commit()
        db.refresh(obj)
        return obj

    def upsert_one(self, db: Session, filter: F, data: C | U) -> M:
        obj = self.find_one(db, filter)
        if obj:
            for k, v in data.items():  # type: ignore[attr-defined]
                setattr(obj, k, v)
            db.commit()
            db.refresh(obj)
            return obj

        new_obj = self.model(**data)
        db.add(new_obj)
        db.commit()
        db.refresh(new_obj)
        return new_obj

    # ========================
    # Delete
    # ========================
    def delete_by_id(self, db: Session, id: int) -> bool:
        obj = db.get(self.model, id)
        if not obj:
            return False
        db.delete(obj)
        db.commit()
        return True

    def delete_one(self, db: Session, filter: F) -> bool:
        obj = self.find_one(db, filter)
        if not obj:
            return False
        db.delete(obj)
        db.commit()
        return True
