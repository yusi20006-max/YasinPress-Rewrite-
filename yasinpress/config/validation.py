"""Configuration validation."""

from typing import Any


def require_keys(config: dict[str, Any], keys: set[str]) -> None:
    """Require keys in a configuration mapping."""
    missing = keys - set(config)
    if missing:
        raise ValueError(f"Missing configuration keys: {', '.join(sorted(missing))}")
