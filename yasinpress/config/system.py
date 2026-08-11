"""Merged configuration system."""

from typing import Any

from .loaders import load_env, load_json, load_yaml


def load_config(json_path: str | None = None, yaml_path: str | None = None) -> dict[str, Any]:
    """Load configuration from JSON, YAML, and environment."""
    config: dict[str, Any] = {}
    if json_path:
        config.update(load_json(json_path))
    if yaml_path:
        config.update(load_yaml(yaml_path))
    config.update(load_env())
    return config
