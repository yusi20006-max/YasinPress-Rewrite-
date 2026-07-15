"""API response helpers."""
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class Response:
    """REST-style response object."""
    status_code: int
    body: dict[str, Any]


def ok(body: dict[str, Any]) -> Response:
    """Return a 200 response."""
    return Response(200, body)
