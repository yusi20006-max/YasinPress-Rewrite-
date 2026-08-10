from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from yasinpress.database.models import Article


@dataclass(frozen=True)
class AIResult:
    title: str
    content: str
    provider: str
    success: bool = True
    error: str | None = None


class AIProvider(ABC):
    """Optional AI enrichment contract; failures must remain non-fatal."""

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def enrich(self, article: Article) -> AIResult:
        raise NotImplementedError
