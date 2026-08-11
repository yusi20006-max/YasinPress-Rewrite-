"""Source registry."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    """RSS source definition."""

    name: str
    url: str
    enabled: bool = True


class SourceManager:
    """Manage configured sources."""

    def __init__(self, sources: list[Source] | None = None) -> None:
        self._sources = sources or []

    def add(self, source: Source) -> None:
        """Register a source."""
        self._sources.append(source)

    def enabled(self) -> list[Source]:
        """Return enabled sources."""
        return [source for source in self._sources if source.enabled]
