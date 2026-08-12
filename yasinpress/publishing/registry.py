from __future__ import annotations

from collections.abc import Iterable

from yasinpress.publishing import Publisher


class PublisherRegistry:
    """Explicit destination registry used by the queue worker."""

    def __init__(self, publishers: Iterable[Publisher] = ()) -> None:
        self._publishers: dict[str, Publisher] = {}
        for publisher in publishers:
            self.register(publisher)

    def register(self, publisher: Publisher) -> None:
        name = publisher.name.strip().lower()
        if not name:
            raise ValueError("publisher name must not be empty")
        if name in self._publishers:
            raise ValueError(f"publisher already registered: {name}")
        self._publishers[name] = publisher

    def get(self, name: str) -> Publisher:
        key = name.strip().lower()
        try:
            return self._publishers[key]
        except KeyError as exc:
            raise KeyError(f"publisher not registered: {key}") from exc

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._publishers))
