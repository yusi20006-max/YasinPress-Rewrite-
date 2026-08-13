"""Transport-neutral API request model."""

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
        values = {k: tuple(v for v in items if v != "") for k, items in parse_qs(parsed.query, keep_blank_values=True).items()}
        return cls(method.upper(), parsed.path or "/", {k.lower(): v for k, v in (headers or {}).items()}, values, body)
    def query_value(self, name: str, default: str | None = None) -> str | None:
        values = self.query.get(name)
        return values[0] if values else default
    @property
    def bearer_token(self) -> str | None:
        scheme, _, token = self.headers.get("authorization", "").partition(" ")
        return token if scheme.lower() == "bearer" and token else None
