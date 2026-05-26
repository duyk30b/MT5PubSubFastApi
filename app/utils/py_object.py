import json
from typing import Any


class PyObject:
    @staticmethod
    def json_load(value: str | None, default: Any) -> Any:
        if not value or value == "null":
            return default
        try:
            return json.loads(value)
        except (TypeError, json.JSONDecodeError):
            return default

    @staticmethod
    def json_dump(value: Any, default: Any = "{}") -> str:
        try:
            return json.dumps(value)
        except (TypeError, OverflowError):
            return default
