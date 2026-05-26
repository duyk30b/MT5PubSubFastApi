from dataclasses import dataclass
from urllib.parse import SplitResult, parse_qsl, urlencode, urlsplit, urlunsplit


@dataclass(slots=True)
class PySplitResult:
    scheme: str
    netloc: str
    path: str
    query: str
    fragment: str


class PyUrl:
    @staticmethod
    def urlsplit(url: str) -> PySplitResult:
        # example url: "postgresql://user:password@localhost:5432/mydatabase?sslmode=require&channel_binding=prefer#abc"
        result: SplitResult = urlsplit(url)
        return PySplitResult(
            scheme=result.scheme,  # example: "postgresql"
            netloc=result.netloc,  # example: "user:password@localhost:5432"
            path=result.path,  # example: "/mydatabase"
            query=result.query,  # example: "sslmode=require&channel_binding=prefer"
            fragment=result.fragment,  # example: "abc"
        )

    @staticmethod
    def urlunsplit(
        scheme: str,  # example: "postgresql+asyncpg"
        netloc: str,  # example: "user:password@localhost:5432"
        path: str | None,  # example: "/mydatabase"
        query: str | None,  # example: "sslmode=require&channel_binding=prefer"
        fragment: str | None,  # example: "abc"
    ) -> str:
        # result: "postgresql+asyncpg://user:password@localhost:5432/mydatabase?sslmode=require&channel_binding=prefer#abc"
        return urlunsplit((scheme, netloc, path or "", query or "", fragment or ""))

    @staticmethod
    def parse_qsl(query: str, keep_blank_values: bool = False) -> list[tuple[str, str]]:
        # example query: "sslmode=require&channel_binding=prefer"
        # result: [('sslmode', 'require'), ('channel_binding', 'prefer')]
        return parse_qsl(query, keep_blank_values=keep_blank_values)

    @staticmethod
    def urlencode(query: list[tuple[str, str]]) -> str:
        # example query: [('sslmode', 'require'), ('channel_binding', 'prefer')]
        # result: "sslmode=require&channel_binding=prefer"
        return urlencode(query)
