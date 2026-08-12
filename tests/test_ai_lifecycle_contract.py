from datetime import UTC, datetime

from yasinpress.ai.base import AIResult, AIProvider
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
    return Article(
        id="YP-TEST-AI",
        title="عنوان اصلی",
        url="https://example.com/news",
        content="متن اصلی",
        source="example",
        published_at=datetime.now(UTC),
    )


def test_ai_disabled_has_explicit_disabled_state() -> None:
    result = ArticleEnricher().enrich(make_article())
    assert result.article.ai_state == "disabled"
    assert result.provider == "none"


def test_provider_failure_falls_back_to_original() -> None:
    result = ArticleEnricher(SafeAIEnricher(FailingProvider())).enrich(make_article())
    assert result.article.ai_state == "fallback_original"
    assert result.article.title == "عنوان اصلی"
    assert result.article.content == "متن اصلی"
    assert result.article.ai_error == "provider unavailable"


def test_successful_rewrite_sets_rewritten_state() -> None:
    result = ArticleEnricher(SafeAIEnricher(RewritingProvider())).enrich(make_article())
    assert result.article.ai_state == "rewritten"
    assert result.article.ai_modified is True
    assert result.article.title == "بازنویسی"
