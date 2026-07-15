"""Logging configuration."""
import logging
from .constants import DEFAULT_LOG_FORMAT


def configure_logging(level: str = "INFO") -> None:
    """Configure root logging with a predictable production format."""
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format=DEFAULT_LOG_FORMAT)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger."""
    return logging.getLogger(name)
