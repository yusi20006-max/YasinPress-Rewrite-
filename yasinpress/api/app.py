"""Minimal but method-aware transport-neutral API router."""

from collections.abc import Callable
from dataclasses import dataclass
from inspect import signature

from .auth import TokenAuth
from .request import Request
from .responses import Response, method_not_allowed, not_found, unauthorized

Handler = Callable[[Request], Response]
LegacyHandler = Callable[[], Response]

@dataclass(frozen=True)
class Route:
    method: str
    handler: Handler
    protected: bool = False

class ApiApp:
    """Route requests without coupling the domain to an HTTP framework."""
    def __init__(self, auth: TokenAuth | None = None) -> None:
        self.routes: dict[tuple[str, str], Route] = {}
        self.auth = auth

    def route(self, path: str, handler: Handler | LegacyHandler, *, method: str = "GET", protected: bool = False) -> None:
        normalized_method = method.upper()
        if not path.startswith("/"):
            raise ValueError("API paths must start with '/'")
        accepts_request = len(signature(handler).parameters) > 0
        def adapted(request: Request) -> Response:
            if accepts_request:
                return handler(request)  # type: ignore[misc]
            return handler()  # type: ignore[call-arg]
        self.routes[(normalized_method, path)] = Route(normalized_method, adapted, protected)

    def handle(self, target: str, *, method: str = "GET", headers: dict[str, str] | None = None, body: dict[str, object] | None = None) -> Response:
        request = Request.from_target(target, method=method, headers=headers, body=body)
        route = self.routes.get((request.method, request.path))
        if route is None:
            allowed = tuple(r.method for (_, p), r in self.routes.items() if p == request.path)
            return method_not_allowed(allowed) if allowed else not_found()
        if route.protected and (self.auth is None or not self.auth.verify(request.bearer_token or "")):
            return unauthorized()
        return route.handler(request)
