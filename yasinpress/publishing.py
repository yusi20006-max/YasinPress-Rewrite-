from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from yasinpress.database.models import Article


@dataclass(frozen=True)
class PublishResult:
    success: bool
    destination: str
    external_id: str | None = None
    error: str | None = None


class Publisher(ABC):
    """Provider-neutral publishing contract."""

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def publish(self, article: Article) -> PublishResult:
        raise NotImplementedError
