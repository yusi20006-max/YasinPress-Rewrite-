"""Publisher abstraction."""
from collections.abc import Protocol

class Publisher(Protocol):
    """Protocol for outbound publishers."""
    def publish(self, message: str) -> bool: ...
