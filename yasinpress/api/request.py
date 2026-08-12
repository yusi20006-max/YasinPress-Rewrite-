"""Small transport-neutral request model for the YasinPress API."""

from dataclasses import dataclass, field
from urllib.parse import parse_qs, urlsplit


@dataclass(frozen=True)
class Request:
    method: str = "GET"
    path: str = "/"
    headers: dict[str, str] = field(default_factory=dict)
    query: dict[str, tuple[str, ...]] = field(default_factory=dict)
    body: dict[str, object] | None = None

    @classmethod
    def from_target(cls, target: str, *, method: str = "GET", headers: dict[str, str] | None = None, body: dict[str, object] | None = None) -> "Request":
        parsed = urlsplit(target)
        values = {key: tuple(item for item in items if item != "") for key, items in parse_qs(parsed.query, keep_blank_values=True).items()}
        return cls(method=method.upper(), path=parsed.path or "/", headers={key.lower(): value for key, value in (headers or {}).items()}, query=values, body=body)

    def query_value(self, name: str, default: str | None = None) -> str | None:
        values = self.query.get(name)
        return values[0] if values else default

    @property
    def bearer_token(self) -> str | None:
        value = self.headers.get("authorization", "")
        scheme, _, token = value.partition(" ")
        return token if scheme.lower() == "bearer" and token else None
