"""Application bootstrap and orchestration."""

from dataclasses import dataclass

from .logger import configure_logging, get_logger
from .paths import ensure_runtime_dirs


@dataclass(frozen=True)
class Application:
    """Coordinates application startup."""

    log_level: str = "INFO"

    def start(self) -> None:
        """Initialize runtime services."""
        ensure_runtime_dirs()
        configure_logging(self.log_level)
        get_logger(__name__).info("YasinPress application started")
