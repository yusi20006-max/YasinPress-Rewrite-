from datetime import datetime, timedelta, timezone
import sqlite3

from yasinpress.ai.mock import FailingAIProvider, MockAIProvider
from yasinpress.ai.safe import SafeAIEnricher
from yasinpress.database.repositories import ArticleRepository
from yasinpress.processing.pipeline import ArticlePipeline
from yasinpress.sources.feed import FeedItem


def repo() -> ArticleRepository:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE articles (id TEXT PRIMARY KEY, title TEXT, url TEXT, content TEXT, source TEXT, published_at TEXT, category TEXT)")
    return ArticleRepository(conn)


def item() -> FeedItem:
    return FeedItem(
        title="خبر فناوری",
        url="https://example.com/ai",
        content="محتوای فناوری",
        published_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )


def test_pipeline_works_with_ai_provider():
    result = ArticlePipeline(repo(), ai=SafeAIEnricher(MockAIProvider())).process(item(), source="test")
    assert result is not None
    assert result.ai_success
    assert result.ai_provider == "mock"


def test_pipeline_survives_ai_failure():
    result = ArticlePipeline(repo(), ai=SafeAIEnricher(FailingAIProvider())).process(item(), source="test")
    assert result is not None
    assert not result.ai_success
    assert result.ai_provider == "failing-mock"
    assert result.article.title == "خبر فناوری"
