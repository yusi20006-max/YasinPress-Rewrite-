from __future__ import annotations

from yasinpress.database.delivery import SQLiteDeliveryRepository
from yasinpress.database.jobs import SQLiteJobRepository
from yasinpress.database.sqlite import SQLiteArticleRepository
from yasinpress.database.state import SQLiteState


class Database:
    """Application database composition root using one shared SQLite connection."""

    def __init__(self, path: str = ":memory:") -> None:
        self.state = SQLiteState(path)
        self.articles = SQLiteArticleRepository(connection=self.state.connection)
        self.jobs = SQLiteJobRepository(self.state.connection)
        self.deliveries = SQLiteDeliveryRepository(self.state.connection)

    def close(self) -> None:
        self.state.close()
