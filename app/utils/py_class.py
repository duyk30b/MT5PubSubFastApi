import json
from typing import Any, TypeVar, cast, get_args, get_origin, get_type_hints

TPyClass = TypeVar("TPyClass", bound="PyClass")


class PyClass:
    def __init__(self, **kwargs):  # type: ignore
        hints = get_type_hints(type(self))

        for field, field_type in hints.items():
            value = kwargs.get(field, None)  # type: ignore

            if value is None:
                if hasattr(type(self), field):
                    value = getattr(type(self), field)

            normalized_type = self._unwrap_optional_type(field_type)

            if (
                isinstance(value, dict)
                and isinstance(normalized_type, type)
                and issubclass(normalized_type, PyClass)
            ):
                value = normalized_type.from_dict(value)  # type: ignore

            setattr(self, field, value)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in self.__dict__.items():
            result[key] = self._serialize_value(value)
        return result

    def to_json_text(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def list_to_json_text(cls, obj_list: list[Any]) -> str:
        serialized_list: list[Any] = []
        for item in obj_list:
            serialized_list.append(cls._serialize_value(item))
        return json.dumps(serialized_list)

    @classmethod
    def from_dict(cls: type[TPyClass], data: dict[str, Any]) -> TPyClass:
        if not isinstance(data, dict):  # type: ignore
            return cls.__new__(cls)

        hints = get_type_hints(cls)
        instance = cls.__new__(cls)

        for key, type_hint in hints.items():
            value: Any = data.get(key, None)

            if value is None:
                setattr(instance, key, None)
                continue

            normalized_hint = cls._unwrap_optional_type(type_hint)

            origin = get_origin(normalized_hint)
            if origin is list:
                args = get_args(normalized_hint)
                item_type = cls._unwrap_optional_type(args[0]) if args else None
                if (
                    isinstance(value, list)
                    and isinstance(item_type, type)
                    and issubclass(item_type, PyClass)
                ):
                    parsed_items: list[Any] = []
                    for item in cast(list[Any], value):
                        if isinstance(item, dict):
                            parsed_items.append(
                                item_type.from_dict(cast(dict[str, Any], item))
                            )
                        else:
                            parsed_items.append(item)
                    value = parsed_items
                setattr(instance, key, value)

            elif isinstance(normalized_hint, type) and issubclass(
                normalized_hint, PyClass
            ):
                if isinstance(value, dict):
                    setattr(
                        instance,
                        key,
                        normalized_hint.from_dict(cast(dict[str, Any], value)),
                    )
                elif isinstance(value, normalized_hint):
                    setattr(instance, key, value)
                else:
                    setattr(instance, key, None)

            else:
                setattr(instance, key, value)

        return instance

    @classmethod
    def list_from_dict_list(
        cls: type[TPyClass], data_list: list[Any]
    ) -> list[TPyClass]:
        if not isinstance(data_list, list):  # type: ignore
            return []
        parsed_list: list[TPyClass] = []
        for item in data_list:
            if isinstance(item, dict):
                parsed_list.append(cls.from_dict(cast(dict[str, Any], item)))
        return parsed_list

    @classmethod
    def from_json_text(cls: type[TPyClass], json_text: str | None) -> TPyClass:
        if json_text is None or json_text == "":
            return cls.__new__(cls)
        try:
            data = json.loads(json_text)
            return cls.from_dict(data)
        except (TypeError, json.JSONDecodeError):
            return cls.__new__(cls)

    @classmethod
    def list_from_json_text(
        cls: type[TPyClass], json_text: str | None
    ) -> list[TPyClass]:
        if json_text is None or json_text == "":
            return []
        try:
            data_list = json.loads(json_text)
            if not isinstance(data_list, list):
                return []
            parsed_list: list[TPyClass] = []
            for item in cast(list[Any], data_list):
                if isinstance(item, dict):
                    parsed_list.append(cls.from_dict(cast(dict[str, Any], item)))
            return parsed_list
        except (TypeError, json.JSONDecodeError):
            return []

    @classmethod
    def _unwrap_optional_type(cls, type_hint: Any) -> Any:
        args = get_args(type_hint)
        if not args:
            return type_hint

        non_none_args = [arg for arg in args if arg is not type(None)]
        if len(non_none_args) == 1 and len(non_none_args) != len(args):
            return non_none_args[0]
        return type_hint

    @classmethod
    def _serialize_value(cls, value: Any) -> Any:
        if isinstance(value, PyClass):
            return value.to_dict()
        if isinstance(value, list):
            serialized_items: list[Any] = []
            for item in cast(list[Any], value):
                serialized_items.append(cls._serialize_value(item))
            return serialized_items
        if isinstance(value, tuple):
            serialized_tuple_items: list[Any] = []
            for item in cast(tuple[Any, ...], value):
                serialized_tuple_items.append(cls._serialize_value(item))
            return serialized_tuple_items
        if isinstance(value, dict):
            serialized_dict: dict[str, Any] = {}
            for key, item in cast(dict[Any, Any], value).items():
                serialized_dict[str(key)] = cls._serialize_value(item)
            return serialized_dict
        return value
