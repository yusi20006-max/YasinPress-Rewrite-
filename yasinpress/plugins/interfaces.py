"""Plugin interfaces."""
from collections.abc import Protocol

class Plugin(Protocol):
    """Plugin contract."""
    name: str
    def activate(self) -> None: ...
