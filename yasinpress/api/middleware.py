"""API middleware helpers."""
from collections.abc import Callable
from .responses import Response

Handler = Callable[[], Response]

def with_error_handling(handler: Handler) -> Response:
    """Convert unexpected exceptions into JSON-style responses."""
    try:
        return handler()
    except Exception as exc:
        return Response(500, {"error": exc.__class__.__name__})
