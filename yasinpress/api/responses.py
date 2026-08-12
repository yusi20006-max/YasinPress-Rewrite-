"""API response helpers."""

from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class Response:
    status_code: int
    body: dict[str, Any]
    headers: dict[str, str] | None = None

def ok(body: dict[str, Any]) -> Response:
    return Response(200, body)

def created(body: dict[str, Any]) -> Response:
    return Response(201, body)

def bad_request(message: str) -> Response:
    return Response(400, {"error": "bad_request", "message": message})

def unauthorized() -> Response:
    return Response(401, {"error": "unauthorized"}, {"WWW-Authenticate": "Bearer"})

def not_found() -> Response:
    return Response(404, {"error": "not_found"})

def method_not_allowed(allowed: tuple[str, ...]) -> Response:
    return Response(405, {"error": "method_not_allowed"}, {"Allow": ", ".join(allowed)})
