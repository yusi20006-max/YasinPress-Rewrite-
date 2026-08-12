"""Provider-agnostic AI intelligence contracts."""

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class AIResult:
    """Structured result returned by an AI provider."""

    title: str | None = None
    summary: str | None = None
    category: str | None = None
    priority: str | None = None
    breaking: bool = False
    metadata: dict[str, object] = field(default_factory=dict)


class AIProvider(Protocol):
    """Minimal provider contract used by the application pipeline."""

    def analyze(self, title: str, content: str) -> AIResult:
        """Analyze one article without owning persistence or publishing."""
        ...


class DisabledAIProvider:
    """Provider used when AI is explicitly disabled."""

    def analyze(self, title: str, content: str) -> AIResult:
        """Return an unchanged result without invoking an external service."""
        return AIResult(metadata={"provider": "disabled"})


class FakeAIProvider:
    """Deterministic provider for tests and local integration checks."""

    def __init__(self, result: AIResult | None = None, error: Exception | None = None):
        self.result = result or AIResult(metadata={"provider": "fake"})
        self.error = error

    def analyze(self, title: str, content: str) -> AIResult:
        """Return the configured deterministic result or raise its configured error."""
        if self.error is not None:
            raise self.error
        return self.result
