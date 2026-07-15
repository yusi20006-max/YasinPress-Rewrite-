"""CLI command dispatch."""
from yasinpress import __version__
from .status import status_text


def dispatch(command: str) -> str:
    """Dispatch a CLI command."""
    if command == "version": return __version__
    return status_text()
