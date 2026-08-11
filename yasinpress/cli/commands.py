"""CLI command dispatch."""

from yasinpress import __version__
from yasinpress.config.runtime import RuntimeConfig

from .status import status_text


def dispatch(command: str) -> str:
    """Dispatch a CLI command without starting the runtime for read-only checks."""
    if command == "version":
        return __version__
    if command == "config":
        cfg = RuntimeConfig.from_env()
        cfg.validate()
        return "configuration: ok"
    if command == "health":
        return status_text()
    if command == "run":
        return "runtime: use the application entrypoint to start"
    return status_text()
