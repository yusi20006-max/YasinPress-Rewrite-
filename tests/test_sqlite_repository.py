from datetime import UTC, datetime

from yasinpress.database.models import Article
from yasinpress.database.sqlite import SQLiteArticleRepository


def test_sqlite_article_repository_round_trip():
    repo = SQLiteArticleRepository()
    article = Article("1", "خبر", "https://example.com", "متن", "feed", datetime.now(UTC), "tech")
    repo.save(article)
    loaded = repo.get("1")
    assert loaded == article
    assert repo.all() == (article,)
    repo.close()


def test_sqlite_save_updates_existing_article():
    repo = SQLiteArticleRepository()
    article = Article("1", "old", "https://example.com", "old", "feed")
    updated = Article("1", "new", "https://example.com", "new", "feed", article.published_at)
    repo.save(article)
    repo.save(updated)
    assert repo.get("1").title == "new"
    assert len(repo.all()) == 1
    repo.close()
