import sqlite3
from datetime import UTC, datetime

import pytest

from yasinpress.database.migrations import migrate
from yasinpress.database.models import Article
from yasinpress.database.repositories import ArticleRepository
from yasinpress.database.sqlite import SQLiteArticleRepository


def _legacy_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE articles (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            content TEXT NOT NULL,
            source TEXT NOT NULL,
            published_at TEXT NOT NULL,
            category TEXT,
            legacy_marker TEXT
        )
        """
    )
    connection.execute(
        "CREATE INDEX idx_articles_legacy_marker ON articles(legacy_marker)"
    )
    connection.execute(
        """
        INSERT INTO articles(id,title,url,content,source,published_at,category,legacy_marker)
        VALUES(?,?,?,?,?,?,?,?)
        """,
        (
            "legacy-1",
            "Legacy",
            "https://example.com/legacy",
            "Body",
            "feed",
            datetime(2026, 8, 14, 10, tzinfo=UTC).isoformat(),
            "news",
            "keep-me",
        ),
    )
    connection.commit()
    return connection


def test_legacy_articles_migration_preserves_data_constraints_and_indexes():
    connection = _legacy_connection()

    migrate(connection)
    migrate(connection)

    published = next(
        row[3]
        for row in connection.execute("PRAGMA table_info(articles)").fetchall()
        if row[1] == "published_at"
    )
    assert published == 0

    row = connection.execute(
        "SELECT title, legacy_marker FROM articles WHERE id='legacy-1'"
    ).fetchone()
    assert row["title"] == "Legacy"
    assert row["legacy_marker"] == "keep-me"

    indexes = {
        row[1]
        for row in connection.execute("PRAGMA index_list(articles)").fetchall()
    }
    assert "idx_articles_legacy_marker" in indexes

    connection.execute(
        "INSERT INTO articles(id,title,url,content,source,published_at) VALUES(?,?,?,?,?,?)",
        ("null-pub", "No date", "https://example.com/null", "Body", "feed", None),
    )
    connection.commit()

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO articles(id,title,url,content,source,published_at) VALUES(?,?,?,?,?,?)",
            (
                "duplicate-url",
                "Duplicate",
                "https://example.com/legacy",
                "Body",
                "feed",
                None,
            ),
        )


def test_repository_adapters_share_legacy_migration_and_lifecycle_state():
    connection = _legacy_connection()
    repository = ArticleRepository(connection)

    now = datetime.now(UTC)
    article = Article(
        id="lifecycle-1",
        title="Lifecycle",
        url="https://example.com/lifecycle",
        content="Body",
        source="feed",
        published_at=None,
        updated_at=now,
        fetched_at=now,
        processed_at=now,
        published_to_channel_at=now,
    )
    repository.save(article)

    loaded = repository.get(article.id)
    assert loaded is not None
    assert loaded.published_at is None
    assert loaded.updated_at == now
    assert loaded.fetched_at == now
    assert loaded.processed_at == now
    assert loaded.published_to_channel_at == now

    # The second adapter must see the already-migrated schema without changing it.
    sqlite_repository = SQLiteArticleRepository(connection=connection)
    loaded_again = sqlite_repository.get(article.id)
    assert loaded_again == loaded
