from __future__ import annotations

from yasinpress.database.delivery import SQLiteDeliveryRepository
from yasinpress.database.jobs import SQLiteJobRepository
from yasinpress.database.sqlite import SQLiteArticleRepository
from yasinpress.database.state import SQLiteState


class Database:
    """Application database composition root."""

    def __init__(self, path: str = ":memory:") -> None:
        self.state = SQLiteState(path)
        self.articles = SQLiteArticleRepository(path) if path == ":memory:" else SQLiteArticleRepository(path)
        # Repositories own their connection today; these attributes establish a stable
        # application boundary for the next migration to a shared unit-of-work.
        self.jobs = SQLiteJobRepository(self.articles.connection)
        self.deliveries = SQLiteDeliveryRepository(self.articles.connection)

    def close(self) -> None:
        self.articles.close()
        self.state.close()
