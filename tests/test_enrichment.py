from datetime import UTC, datetime

from yasinpress.ai.base import AIResult
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


def test_successful_ai_enrichment_preserves_domain_fields_and_records_metadata():
    provider = MockAIProvider()
    result = ArticleEnricher(SafeAIEnricher(provider)).enrich(make_article())
    assert result.ai_success
    assert result.article.title == "Original title"
    assert result.article.content == "Original content"
    assert result.article.category == "technology"
    assert result.article.url == "https://example.com/1"
    assert result.article.ai_state == "rewritten"
    assert result.article.ai_modified is True
    assert result.article.source_metadata["ai_provider"] == provider.name


def test_failed_ai_enrichment_records_fallback_state_without_mutating_provenance():
    original = make_article()
    result = ArticleEnricher(SafeAIEnricher(FailingAIProvider())).enrich(original)
    assert not result.ai_success
    assert result.article.title == original.title
    assert result.article.content == original.content
    assert result.article.url == original.url
    assert result.article.ai_state == "fallback_original"
    assert result.article.ai_modified is False
    assert result.article.ai_error


def test_ai_result_metadata_reaches_article():
    class Provider:
        name = "test-provider"

        def enrich(self, article: Article) -> AIResult:
            return AIResult(
                title="Rewritten title",
                content="Rewritten content",
                provider=self.name,
                success=True,
                summary="Short summary",
                category="world",
                priority="urgent",
                breaking=True,
                metadata={"trace_id": "abc"},
            )

    result = ArticleEnricher(SafeAIEnricher(Provider())).enrich(make_article())
    assert result.article.ai_state == "rewritten"
    assert result.article.ai_modified is True
    assert result.article.title == "Rewritten title"
    assert result.article.category == "world"
    assert result.article.source_metadata["trace_id"] == "abc"
    assert result.article.source_metadata["ai_summary"] == "Short summary"
    assert result.article.source_metadata["ai_priority"] == "urgent"
    assert result.article.source_metadata["ai_breaking"] is True
