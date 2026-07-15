"""Plugin loader."""
import importlib
from .interfaces import Plugin


def load_plugin(path: str) -> Plugin:
    """Load a plugin object from module:attribute syntax."""
    module_name, attribute = path.split(":", 1)
    plugin = getattr(importlib.import_module(module_name), attribute)
    return plugin() if isinstance(plugin, type) else plugin
