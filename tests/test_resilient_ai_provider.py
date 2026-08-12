from yasinpress.ai.base import AIProvider, AIResult
from yasinpress.ai.resilient import AIResiliencePolicy, ResilientAIProvider
from yasinpress.database.models import Article
from datetime import UTC, datetime


ARTICLE = Article(
    id="YP-260101-000001",
    title="Original title",
    url="https://example.com/news",
    content="Original content",
    source="example",
    published_at=datetime(2026, 1, 1, tzinfo=UTC),
)


class FailingProvider(AIProvider):
    @property
    def name(self):
        return "fake"

    def enrich(self, article):
        raise RuntimeError("provider unavailable")


class InvalidProvider(AIProvider):
    @property
    def name(self):
        return "invalid"

    def enrich(self, article):
        return "not-an-ai-result"


def test_provider_failure_becomes_nonfatal_result():
    provider = ResilientAIProvider(FailingProvider(), AIResiliencePolicy(max_attempts=2, timeout_seconds=1))
    result = provider.enrich(ARTICLE)
    assert result.success is False
    assert result.title == ARTICLE.title
    assert result.content == ARTICLE.content
    assert "provider failure" in result.error


def test_invalid_provider_response_is_rejected_without_leaking_into_domain():
    provider = ResilientAIProvider(InvalidProvider(), AIResiliencePolicy(max_attempts=1, timeout_seconds=1))
    result = provider.enrich(ARTICLE)
    assert result.success is False
    assert result.error == "Invalid AI provider response"
