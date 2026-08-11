import sqlite3
from datetime import UTC, datetime, timedelta

from yasinpress.database.repositories import ArticleRepository
from yasinpress.processing.pipeline import ArticlePipeline
from yasinpress.sources.feed import FeedItem


def make_repo() -> ArticleRepository:
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE articles (id TEXT PRIMARY KEY, title TEXT, url TEXT, content TEXT, source TEXT, published_at TEXT, category TEXT)"
    )
    return ArticleRepository(conn)


def item(title: str, *, age_hours: int = 1) -> FeedItem:
    return FeedItem(
        title=title,
        url="https://example.com/news",
        content="فناوری و خبر مهم",
        published_at=datetime.now(UTC) - timedelta(hours=age_hours),
    )


def test_pipeline_processes_article_end_to_end():
    repo = make_repo()
    result = ArticlePipeline(repo).process(item("فوری: خبر فناوری"), source="test")
    assert result is not None
    assert result.article.category == "technology"
    assert result.priority.level == "high"
    assert result.breaking.is_breaking
    assert repo.exists(result.article.id)


def test_pipeline_rejects_stale_article():
    repo = make_repo()
    assert ArticlePipeline(repo).process(item("خبر قدیمی", age_hours=48), source="test") is None


def test_pipeline_rejects_duplicate_article():
    repo = make_repo()
    pipeline = ArticlePipeline(repo)
    first = pipeline.process(item("خبر فناوری"), source="test")
    assert first is not None
    assert pipeline.process(item("خبر فناوری"), source="test") is None
