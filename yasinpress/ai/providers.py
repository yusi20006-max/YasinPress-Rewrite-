"""AI provider abstractions."""

from collections.abc import Protocol


class AIProvider(Protocol):
    """Protocol implemented by AI providers."""

    def complete(self, prompt: str) -> str: ...


class RuleBasedProvider:
    """Deterministic local provider for offline operation."""

    def complete(self, prompt: str) -> str:
        """Return a concise deterministic completion."""
        return prompt.strip()[:240]
