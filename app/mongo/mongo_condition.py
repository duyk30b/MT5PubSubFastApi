from typing import Any, Dict, List, Tuple, cast
from bson import ObjectId


OPERATOR_MAP: Dict[str, str] = {
    "GT": "$gt",
    "GTE": "$gte",
    "LT": "$lt",
    "LTE": "$lte",
    "EQUAL": "$eq",
    "NOT": "$ne",
}


class MongoCondition:
    """
    Convert condition dict (wrapped syntax) sang MongoDB filter dict.

    Wrapped syntax ví dụ:
        {
            "price": {"GT": 100, "LTE": 500},
            "name":  {"LIKE": "foo"},
            "status": "active",
            "OR": [
                {"tag": {"IN": ["a", "b"]}},
                {"tag": {"IS_NULL": True}},
            ]
        }

    MongoDB filter output:
        {
            "price": {"$gt": 100, "$lte": 500},
            "name":  {"$regex": ".*foo.*", "$options": "i"},
            "status": "active",
            "$or": [
                {"tag": {"$in": ["a", "b"]}},
                {"tag": {"$eq": None}},
            ]
        }
    """

    def _parse_field(self, column: str, target: Any) -> Dict[str, Any]:
        """
        Parse 1 field: (column, target) → {column: mongo_expr}
        target có thể là:
          - primitive (str, int, float, bool)  → exact match
          - None                               → {$or: [null, not exists]}
          - dict với operators                 → parse từng operator
        """
        # None → null or not exists
        if target is None:
            return {column: {"$or": [{column: None}, {column: {"$exists": False}}]}}

        # Primitive → exact match
        if isinstance(target, (str, int, float, bool)):
            if (
                column == "_id"
                and isinstance(target, str)
                and ObjectId.is_valid(target)
            ):
                return {column: ObjectId(target)}
            return {column: target}

        # Dict → parse operators
        if isinstance(target, dict):
            if not target:
                return {}

            rule_column: Dict[str, Any] = {}

            for rule, value in cast(dict[Any, Any], target).items():
                if value is None:
                    continue

                # Comparison operators
                if rule in OPERATOR_MAP:
                    rule_column[OPERATOR_MAP[rule]] = value
                    continue

                if rule == "IS_NULL":
                    if value is True:
                        rule_column["$eq"] = None
                    elif value is False:
                        rule_column["$exists"] = True
                        rule_column["$ne"] = None
                    continue

                if rule == "NOT_NULL":
                    if value is True:
                        rule_column["$exists"] = True
                        rule_column["$ne"] = None
                    elif value is False:
                        rule_column["$eq"] = None
                    continue

                if rule == "BETWEEN":
                    rule_column["$gte"] = value[0]
                    rule_column["$lte"] = value[1]
                    continue

                if rule == "IN":
                    rule_column["$in"] = value if value else []
                    continue

                if rule == "NOT_IN":
                    rule_column["$nin"] = value
                    continue

                if rule == "LIKE":
                    rule_column["$regex"] = f".*{value}.*"
                    rule_column["$options"] = "i"
                    continue

            if not rule_column:
                # Dict nhưng không có operator nào hợp lệ → raw value
                return {column: target}

            return {column: rule_column}

        # List, tuple, ... → raw value
        return {column: target}

    def get_filter_options(self, condition: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert toàn bộ condition dict sang MongoDB filter.
        Xử lý đệ quy OR / AND.
        """
        if not condition:
            return {}

        result: Dict[str, Any] = {}

        for column, target in condition.items():
            # OR / AND — xử lý đệ quy
            if column == "OR":
                if target:
                    result["$or"] = [self.get_filter_options(c) for c in target]
                continue

            if column == "AND":
                if target:
                    result["$and"] = [self.get_filter_options(c) for c in target]
                continue

            # Chuẩn hoá id → _id
            real_column = "_id" if column == "id" else column

            # Bỏ qua nếu target là undefined-like sentinel
            # (Python không có undefined, nhưng caller có thể truyền vào)
            # target=None được xử lý bên trong _parse_field

            parsed = self._parse_field(real_column, target)
            result.update(parsed)

        return result

    def get_sort_options(self, sort: Dict[str, str]) -> List[Tuple[str, int]]:
        """
        Convert sort dict sang list of (field, direction) cho PyMongo.
        {"createdAt": "DESC", "name": "ASC"} → [("createdAt", -1), ("name", 1)]
        """
        result: List[Tuple[str, int]] = []
        for key, value in sort.items():
            real_key = "_id" if key == "id" else key
            if value == "ASC":
                result.append((real_key, 1))
            elif value == "DESC":
                result.append((real_key, -1))
        return result
