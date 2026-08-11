"""Article summarization."""

from .providers import AIProvider


class Summarizer:
    """Generate article summaries."""

    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider

    def summarize(self, text: str) -> str:
        """Summarize text."""
        return self.provider.complete(f"Summarize: {text}")
