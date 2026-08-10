"""Publishing contracts and result types."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from yasinpress.database.models import Article


@dataclass(frozen=True)
class PublishResult:
    success: bool
    destination: str
    external_id: str | None = None
    error: str | None = None


class Publisher(Protocol):
    @property
    def name(self) -> str: ...

    def publish(self, article: Article) -> PublishResult: ...


__all__ = ["PublishResult", "Publisher"]
