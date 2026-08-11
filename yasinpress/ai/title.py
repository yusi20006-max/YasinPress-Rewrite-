"""Title optimization."""


class TitleOptimizer:
    """Optimize article titles for publication."""

    def optimize(self, title: str) -> str:
        """Return a trimmed title with title casing preserved."""
        return title.strip()[:100]
