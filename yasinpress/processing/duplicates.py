"""Duplicate detection."""
from collections.abc import Protocol
from yasinpress.database.models import Article

class ArticleExistence(Protocol):
    """Protocol for duplicate lookups."""
    def exists(self, article_id: str) -> bool: ...

class DuplicateDetector:
    """Detect already processed articles."""
    def __init__(self, repository: ArticleExistence) -> None:
        self.repository = repository

    def is_duplicate(self, article: Article) -> bool:
        """Return whether an article has already been stored."""
        return self.repository.exists(article.id)
