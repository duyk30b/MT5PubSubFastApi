from datetime import datetime, timedelta
from typing import Union, Optional

TimeInput = Union[str, int, float, datetime]


class PyTimer:
    @staticmethod
    def _to_datetime(time: TimeInput) -> datetime:
        if isinstance(time, datetime):
            return time

        # unix timestamp
        if isinstance(time, (int, float)):
            return (
                datetime.fromtimestamp(time / 1000)
                if time > 1e12
                else datetime.fromtimestamp(time)
            )

        # ISO string
        return datetime.fromisoformat(time.replace("Z", "+00:00")).replace(tzinfo=None)

    @staticmethod
    def _get_offset(
        time: datetime,
        utc_offset: Optional[float],
    ) -> float:
        if utc_offset is not None:
            return utc_offset

        offset = datetime.now().astimezone().utcoffset()

        return offset.total_seconds() / 3600 if offset else 0

    @staticmethod
    def _move_time(
        time: datetime,
        utc_offset: float,
    ) -> datetime:
        return time + timedelta(hours=utc_offset)

    @staticmethod
    def start_of_date(
        time: TimeInput,
        utc_offset: Optional[float] = None,
    ) -> datetime:
        time = PyTimer._to_datetime(time)
        utc_offset = PyTimer._get_offset(time, utc_offset)

        moved = PyTimer._move_time(time, utc_offset)

        result = moved.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        return result - timedelta(hours=utc_offset)

    @staticmethod
    def end_of_date(
        time: TimeInput,
        utc_offset: Optional[float] = None,
    ) -> datetime:
        time = PyTimer._to_datetime(time)
        utc_offset = PyTimer._get_offset(time, utc_offset)

        moved = PyTimer._move_time(time, utc_offset)

        result = moved.replace(
            hour=23,
            minute=59,
            second=59,
            microsecond=999999,
        )

        return result - timedelta(hours=utc_offset)

    @staticmethod
    def start_of_month(
        time: TimeInput,
        utc_offset: Optional[float] = None,
    ) -> datetime:
        time = PyTimer._to_datetime(time)
        utc_offset = PyTimer._get_offset(time, utc_offset)

        moved = PyTimer._move_time(time, utc_offset)

        result = moved.replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        return result - timedelta(hours=utc_offset)

    @staticmethod
    def end_of_month(
        time: TimeInput,
        utc_offset: Optional[float] = None,
    ) -> datetime:
        time = PyTimer._to_datetime(time)
        utc_offset = PyTimer._get_offset(time, utc_offset)

        moved = PyTimer._move_time(time, utc_offset)

        if moved.month == 12:
            next_month = moved.replace(
                year=moved.year + 1,
                month=1,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )
        else:
            next_month = moved.replace(
                month=moved.month + 1,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

        result = next_month - timedelta(microseconds=1)

        return result - timedelta(hours=utc_offset)

    @staticmethod
    def start_of_year(
        time: TimeInput,
        utc_offset: Optional[float] = None,
    ) -> datetime:
        time = PyTimer._to_datetime(time)
        utc_offset = PyTimer._get_offset(time, utc_offset)

        moved = PyTimer._move_time(time, utc_offset)

        result = moved.replace(
            month=1,
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        return result - timedelta(hours=utc_offset)

    @staticmethod
    def end_of_year(
        time: TimeInput,
        utc_offset: Optional[float] = None,
    ) -> datetime:
        time = PyTimer._to_datetime(time)
        utc_offset = PyTimer._get_offset(time, utc_offset)

        moved = PyTimer._move_time(time, utc_offset)

        next_year = moved.replace(
            year=moved.year + 1,
            month=1,
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        result = next_year - timedelta(microseconds=1)

        return result - timedelta(hours=utc_offset)

    @staticmethod
    def info(
        time: TimeInput,
        utc_offset: Optional[float] = None,
    ):
        time = PyTimer._to_datetime(time)
        utc_offset = PyTimer._get_offset(time, utc_offset)

        moved = PyTimer._move_time(time, utc_offset)

        return {
            "year": moved.year,
            "month": moved.month - 1,  # giống JS
            "date": moved.day,
            "hour": moved.hour,
            "minute": moved.minute,
            "second": moved.second,
        }

    @staticmethod
    def text_to_time(
        text: str,
        pattern: str,
        utc_offset: Optional[float] = None,
    ) -> datetime:
        def extract(
            token: str,
            length: int,
            default: int = 0,
        ):
            idx = pattern.find(token)

            return int(text[idx : idx + length]) if idx != -1 else default

        year = extract("YYYY", 4, 1970)
        month = extract("MM", 2, 1)
        day = extract("DD", 2, 1)
        hour = extract("hh", 2, 0)
        minute = extract("mm", 2, 0)
        second = extract("ss", 2, 0)
        ms = extract("xxx", 3, 0)

        time = datetime(
            year,
            month,
            day,
            hour,
            minute,
            second,
            ms * 1000,
        )

        utc_offset = PyTimer._get_offset(
            time,
            utc_offset,
        )

        # local -> UTC
        return time - timedelta(hours=utc_offset)

    @staticmethod
    def time_to_text(
        time: Optional[TimeInput],
        pattern: str = "DD/MM/YYYY",
        utc_offset: Optional[float] = None,
    ) -> str:
        if time is None or time == "":
            return ""

        try:
            time = PyTimer._to_datetime(time)
        except Exception:
            return "Invalid Date"

        utc_offset = PyTimer._get_offset(
            time,
            utc_offset,
        )

        moved = PyTimer._move_time(
            time,
            utc_offset,
        )

        rules = {
            "YYYY": f"{moved.year}",
            "YY": f"{moved.year}"[-2:],
            "MM": f"{moved.month:02}",
            "DD": f"{moved.day:02}",
            "hh": f"{moved.hour:02}",
            "mm": f"{moved.minute:02}",
            "ss": f"{moved.second:02}",
            "xxx": f"{moved.microsecond // 1000:03}",
        }

        result = pattern

        for key, value in rules.items():
            result = result.replace(
                key,
                value,
            )

        return result


# Example
# time = "2023-09-20T22:39:46.711Z"
# print("=============================")
# print(PyTimer.start_of_date(time, 7))
# print(PyTimer.end_of_date(time, 7))
# print("=============================")
# print(PyTimer.start_of_date(time))
# print(PyTimer.end_of_date(time))

# print("=============================")
# print(PyTimer.start_of_month(time, 7))
# print(PyTimer.end_of_month(time, 7))
# print("=============================")
# print(PyTimer.start_of_month(time))
# print(PyTimer.end_of_month(time))

# print("=============================")
# print(PyTimer.start_of_year(time, 7))
# print(PyTimer.end_of_year(time, 7))
# print("=============================")
# print(PyTimer.start_of_year(time))
# print(PyTimer.end_of_year(time))
# print("=============================")
# print(
#     PyTimer.text_to_time(
#         "21/09/2023 05:45:46",
#         "DD/MM/YYYY hh:mm:ss",
#         7
#     )
# )
# print(
#     PyTimer.text_to_time(
#         "21/09/2023 05:45:46",
#         "DD/MM/YYYY hh:mm:ss"
#     )
# )
# print("=============================")
# print(
#     PyTimer.time_to_text(
#         time,
#         "DD/MM/YYYY hh:mm:ss",
#         7
#     )
# )
# print(
#     PyTimer.time_to_text(
#         time,
#         "DD/MM/YYYY hh:mm:ss"
#     )
# )
