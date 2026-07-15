"""Minimal REST-style router."""
from collections.abc import Callable
from .responses import Response

class ApiApp:
    """Routes paths to handlers."""
    def __init__(self) -> None:
        self.routes: dict[str, Callable[[], Response]] = {}
    def route(self, path: str, handler: Callable[[], Response]) -> None:
        """Register a path handler."""
        self.routes[path] = handler
    def handle(self, path: str) -> Response:
        """Handle a path."""
        handler = self.routes.get(path)
        return handler() if handler else Response(404, {"error": "not_found"})
