from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from yasinpress.database.models import Article


@dataclass(frozen=True)
class AIResult:
    """Structured provider result used by the processing pipeline."""

    title: str | None = None
    content: str | None = None
    provider: str = "none"
    success: bool = True
    error: str | None = None
    summary: str | None = None
    category: str | None = None
    priority: str | None = None
    breaking: bool = False
    metadata: dict[str, object] = field(default_factory=dict)


class AIProvider(ABC):
    """Optional AI enrichment contract; failures must remain non-fatal."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the stable provider identifier."""
        raise NotImplementedError

    @abstractmethod
    def enrich(self, article: Article) -> AIResult:
        """Analyze or rewrite an article without publishing it."""
        raise NotImplementedError
