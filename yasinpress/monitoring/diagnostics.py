"""Diagnostics collection."""
import platform


def collect_diagnostics() -> dict[str, str]:
    """Collect runtime diagnostic values."""
    return {"python": platform.python_version(), "platform": platform.platform()}
