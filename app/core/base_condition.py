from typing import Generic, List, Literal, TypedDict, TypeVar

SortOrder = Literal["ASC", "DESC", 1, -1]

T = TypeVar("T")


class FieldCondition(TypedDict, Generic[T], total=False):
    """
    Operator condition cho 1 field.
    Ví dụ: price = {"GT": 100, "LTE": 500}
            name  = {"LIKE": "foo"}
            tags  = {"IN": ["a", "b"]}
    """

    GT: T  # >
    GTE: T  # >=
    LT: T  # <
    LTE: T  # <=
    EQUAL: T  # ==
    NOT: T  # !=
    IS_NULL: bool  # IS_NULL=True  → field is null
    NOT_NULL: bool  # NOT_NULL=True → field is not null
    LIKE: str
    IN: List[T]
    NOT_IN: List[T]
    BETWEEN: List[T]  # (min, max)
