from yasinpress.ai.base import AIProvider, AIResult
from yasinpress.ai.fallback import FallbackAIProvider
from yasinpress.database.models import Article


class Provider(AIProvider):
    def __init__(self, name, result=None, error=None):
        self._name = name
        self.result = result
        self.error = error

    @property
    def name(self):
        return self._name

    def enrich(self, article):
        if self.error:
            raise RuntimeError(self.error)
        return self.result


def article():
    return Article(
        id="a1", title="title", url="https://example.com/1", content="content",
        source="source", published_at=None, category="normal"
    )


def test_fallback_uses_next_provider_after_exception():
    result = AIResult("new", "content", "second", success=True)
    chain = FallbackAIProvider([Provider("first", error="down"), Provider("second", result=result)])
    assert chain.enrich(article()) == result


def test_fallback_returns_failure_after_all_providers_fail():
    chain = FallbackAIProvider([
        Provider("first", error="down"),
        Provider("second", result=AIResult("t", "c", "second", success=False, error="rejected")),
    ])
    result = chain.enrich(article())
    assert not result.success
    assert "first: down" in result.error
    assert "second: rejected" in result.error
