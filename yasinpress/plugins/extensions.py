"""Extension registry."""
from .interfaces import Plugin

class ExtensionRegistry:
    """Keeps activated plugins."""
    def __init__(self) -> None:
        self.plugins: dict[str, Plugin] = {}
    def register(self, plugin: Plugin) -> None:
        """Register and activate a plugin."""
        plugin.activate(); self.plugins[plugin.name] = plugin
