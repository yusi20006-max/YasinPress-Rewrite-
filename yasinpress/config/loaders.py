"""Configuration loaders."""
import json, os
from pathlib import Path
from typing import Any
import yaml


def load_json(path: str) -> dict[str, Any]:
    """Load JSON configuration."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_yaml(path: str) -> dict[str, Any]:
    """Load YAML configuration."""
    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}


def load_env(prefix: str = "YASINPRESS_") -> dict[str, str]:
    """Load prefixed environment variables."""
    return {key.removeprefix(prefix).lower(): value for key, value in os.environ.items() if key.startswith(prefix)}
