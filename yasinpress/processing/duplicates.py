"""Duplicate detection services."""
from __future__ import annotations

from collections.abc import Protocol, Sequence
from dataclasses import dataclass
from difflib import SequenceMatcher

from yasinpress.database.models import Article


class ArticleExistence(Protocol):
    """Protocol for exact duplicate lookups."""

    def exists(self, article_id: str) -> bool: ...


@dataclass(frozen=True)
class DuplicateMatch:
    """Result of a title-similarity duplicate check."""

    is_duplicate: bool
    score: float
    matched_index: int | None = None


class DuplicateDetector:
    """Detect exact IDs and near-duplicate article titles."""

    def __init__(self, repository: ArticleExistence, threshold: float = 0.85) -> None:
        if not 0 <= threshold <= 1:
            raise ValueError("threshold must be between 0 and 1")
        self.repository = repository
        self.threshold = threshold

    def is_duplicate(self, article: Article) -> bool:
        """Return whether an article ID has already been stored."""
        return self.repository.exists(article.id)

    def compare_title(self, title: str, existing_titles: Sequence[str]) -> DuplicateMatch:
        """Detect near-duplicate titles using normalized similarity."""
        normalized = self._normalize(title)
        if not normalized:
            return DuplicateMatch(False, 0.0)

        best_score = 0.0
        best_index: int | None = None
        for index, existing in enumerate(existing_titles):
            candidate = self._normalize(existing)
            if not candidate:
                continue
            score = SequenceMatcher(None, normalized, candidate).ratio()
            if score > best_score:
                best_score = score
                best_index = index

        return DuplicateMatch(best_score >= self.threshold, best_score, best_index)

    @staticmethod
    def _normalize(value: str) -> str:
        return " ".join(value.casefold().split())
