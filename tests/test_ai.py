from datetime import datetime, timezone

from yasinpress.ai.base import AIResult
from yasinpress.ai.mock import FailingAIProvider, MockAIProvider
from yasinpress.ai.safe import SafeAIEnricher
from yasinpress.database.models import Article


def article() -> Article:
    return Article(
        id="1",
        title=" خبر تست ",
        url="https://example.com/1",
        content=" محتوای تست ",
        source="test",
        published_at=datetime.now(timezone.utc),
    )


def test_mock_provider_succeeds():
    result = SafeAIEnricher(MockAIProvider()).enrich(article())
    assert result == AIResult("خبر تست", "محتوای تست", "mock")


def test_missing_provider_is_non_fatal():
    result = SafeAIEnricher().enrich(article())
    assert not result.success
    assert result.provider == "none"


def test_provider_failure_is_non_fatal():
    result = SafeAIEnricher(FailingAIProvider()).enrich(article())
    assert not result.success
    assert result.provider == "failing-mock"
    assert "simulated" in (result.error or "")
