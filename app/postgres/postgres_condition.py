from typing import Any, Dict, List, Type, cast

from sqlalchemy import and_, asc, desc, or_


class PostgresCondition:
    """
    Convert condition dict (wrapped syntax) sang SQLAlchemy filter expressions.

    Wrapped syntax ví dụ:
        {
            "price": {"GT": 100, "LTE": 500},
            "name":  {"LIKE": "foo"},
            "is_active": {"EQUAL": True},
            "OR": [
                {"tag": {"IN": ["a", "b"]}},
                {"tag": {"IS_NULL": True}},
            ]
        }
    """

    def _get_column(self, model: Type[Any], column: str) -> Any:
        col = getattr(model, column, None)
        if col is None:
            raise ValueError(f"Column '{column}' not found on model '{model.__name__}'")
        return col

    def _parse_field(self, model: Type[Any], column: str, target: Any) -> Any:
        """
        Parse 1 field: (column, target) → SQLAlchemy expression
        target có thể là:
          - primitive (str, int, float, bool) → exact match
          - None                              → col.is_(None)
          - dict với operators                → parse từng operator
        """
        col = self._get_column(model, column)

        # None → IS NULL
        if target is None:
            return col.is_(None)

        # Primitive → exact match
        if isinstance(target, (str, int, float, bool)):
            return col == target

        # Dict → parse operators
        if isinstance(target, dict):
            if not target:
                return None

            clauses: List[Any] = []

            for rule, value in cast(dict[Any, Any], target).items():
                if value is None:
                    continue

                if rule == "GT":
                    clauses.append(col > value)
                elif rule == "GTE":
                    clauses.append(col >= value)
                elif rule == "LT":
                    clauses.append(col < value)
                elif rule == "LTE":
                    clauses.append(col <= value)
                elif rule in ("EQUAL", "EQ"):
                    clauses.append(col == value)
                elif rule == "NOT":
                    clauses.append(col != value)
                elif rule == "IS_NULL":
                    if value is True:
                        clauses.append(col.is_(None))
                    elif value is False:
                        clauses.append(col.isnot(None))
                elif rule == "NOT_NULL":
                    if value is True:
                        clauses.append(col.isnot(None))
                    elif value is False:
                        clauses.append(col.is_(None))
                elif rule == "LIKE":
                    clauses.append(col.ilike(f"%{value}%"))
                elif rule == "IN":
                    clauses.append(col.in_(value if value else []))
                elif rule == "NOT_IN":
                    clauses.append(col.notin_(value))
                elif rule == "BETWEEN":
                    clauses.append(col.between(value[0], value[1]))

            if not clauses:
                return None
            if len(clauses) == 1:
                return clauses[0]
            return and_(*clauses)

        return col == target

    def get_filter_clauses(
        self, model: Type[Any], condition: Dict[str, Any]
    ) -> List[Any]:
        """
        Convert toàn bộ condition dict sang list SQLAlchemy filter expressions.
        Xử lý đệ quy OR / AND.
        """
        if not condition:
            return []

        clauses: List[Any] = []

        for column, target in condition.items():
            if column == "OR":
                if target:
                    sub = [and_(*self.get_filter_clauses(model, c)) for c in target]
                    clauses.append(or_(*sub))
                continue

            if column == "AND":
                if target:
                    sub = [and_(*self.get_filter_clauses(model, c)) for c in target]
                    clauses.append(and_(*sub))
                continue

            expr = self._parse_field(model, column, target)
            if expr is not None:
                clauses.append(expr)

        return clauses

    def get_sort_clauses(self, model: Type[Any], sort: Dict[str, str]) -> List[Any]:
        """
        Convert sort dict sang list SQLAlchemy order_by expressions.
        {"created_at": "DESC", "name": "ASC"} → [desc(Model.created_at), asc(Model.name)]
        """
        clauses: List[Any] = []
        for column, direction in sort.items():
            col = self._get_column(model, column)
            if str(direction).upper() == "DESC":
                clauses.append(desc(col))
            else:
                clauses.append(asc(col))
        return clauses
