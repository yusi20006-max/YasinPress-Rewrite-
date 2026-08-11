from datetime import UTC, datetime

from yasinpress.ai.mock import FailingAIProvider, MockAIProvider
from yasinpress.ai.safe import SafeAIEnricher
from yasinpress.database.models import Article
from yasinpress.processing.enrichment import ArticleEnricher


def make_article() -> Article:
    return Article(
        id="1",
        title="Original title",
        url="https://example.com/1",
        content="Original content",
        source="test",
        published_at=datetime.now(UTC),
        category="technology",
    )


def test_successful_ai_enrichment_preserves_domain_fields():
    result = ArticleEnricher(SafeAIEnricher(MockAIProvider())).enrich(make_article())
    assert result.ai_success
    assert result.article.title == "Original title"
    assert result.article.content == "Original content"
    assert result.article.category == "technology"
    assert result.article.url == "https://example.com/1"


def test_failed_ai_enrichment_returns_original_article():
    original = make_article()
    result = ArticleEnricher(SafeAIEnricher(FailingAIProvider())).enrich(original)
    assert not result.ai_success
    assert result.article == original
