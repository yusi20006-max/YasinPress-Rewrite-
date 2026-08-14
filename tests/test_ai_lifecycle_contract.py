from datetime import UTC, datetime

from yasinpress.ai.base import AIProvider, AIResult
from yasinpress.ai.safe import SafeAIEnricher
from yasinpress.database.models import Article
from yasinpress.processing.enrichment import ArticleEnricher


class FailingProvider(AIProvider):
    @property
    def name(self) -> str:
        return "fake"

    def enrich(self, article: Article) -> AIResult:
        raise RuntimeError("provider unavailable")


class RewritingProvider(AIProvider):
    @property
    def name(self) -> str:
        return "fake"

    def enrich(self, article: Article) -> AIResult:
        return AIResult("بازنویسی", "خلاصه", self.name)


def make_article() -> Article:
    now = datetime(2026, 8, 14, 10, 0, tzinfo=UTC)
    return Article(
        id="YP-TEST-AI",
        title="عنوان اصلی",
        url="https://example.com/news",
        content="متن اصلی",
        source="example",
        published_at=datetime(2026, 8, 14, 9, 0, tzinfo=UTC),
        updated_at=datetime(2026, 8, 14, 9, 30, tzinfo=UTC),
        fetched_at=datetime(2026, 8, 14, 9, 45, tzinfo=UTC),
        processed_at=now,
        published_to_channel_at=datetime(2026, 8, 14, 10, 5, tzinfo=UTC),
    )


def test_ai_disabled_has_explicit_disabled_state() -> None:
    result = ArticleEnricher().enrich(make_article())
    assert result.article.ai_state == "disabled"
    assert result.provider == "none"


def test_provider_failure_falls_back_to_original() -> None:
    article = make_article()
    result = ArticleEnricher(SafeAIEnricher(FailingProvider())).enrich(article)
    assert result.article.ai_state == "fallback_original"
    assert result.article.title == "عنوان اصلی"
    assert result.article.content == "متن اصلی"
    assert result.article.ai_error == "provider unavailable"
    assert result.article.updated_at == article.updated_at
    assert result.article.fetched_at == article.fetched_at
    assert result.article.processed_at == article.processed_at
    assert result.article.published_to_channel_at == article.published_to_channel_at


def test_successful_rewrite_sets_rewritten_state() -> None:
    article = make_article()
    result = ArticleEnricher(SafeAIEnricher(RewritingProvider())).enrich(article)
    assert result.article.ai_state == "rewritten"
    assert result.article.ai_modified is True
    assert result.article.title == "بازنویسی"
    assert result.article.updated_at == article.updated_at
    assert result.article.fetched_at == article.fetched_at
    assert result.article.processed_at == article.processed_at
    assert result.article.published_to_channel_at == article.published_to_channel_at
