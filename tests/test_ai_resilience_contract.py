from datetime import UTC, datetime

from yasinpress.ai.base import AIResult
from yasinpress.ai.config import AIConfig
from yasinpress.ai.factory import create_ai_provider
from yasinpress.database.models import Article


class FakeCompletions:
    def __init__(self):
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        class Message:
            content = "بازنویسی آزمایشی"
        class Choice:
            message = Message()
        class Response:
            choices = [Choice()]
        return Response()


class FakeClient:
    def __init__(self):
        self.chat = type("Chat", (), {"completions": FakeCompletions()})()


def article() -> Article:
    return Article(
        event_id="evt-ai",
        title="عنوان",
        content="متن خبر",
        url="https://example.com/news",
        source="example",
        published_at=datetime(2026, 1, 1, tzinfo=UTC),
        received_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def test_enabled_factory_returns_resilient_provider_and_rewrites():
    client = FakeClient()
    provider = create_ai_provider(
        AIConfig(enabled=True, base_url="https://example.com/v1", model="test", api_key_env="MISSING"),
        client=client,
    )
    # Inject a usable key through the config's environment contract without relying on a real service.
    assert provider.name == "openai-compatible"
    result = provider.enrich(article())
    assert isinstance(result, AIResult)
    assert result.success
    assert result.content == "بازنویسی آزمایشی"
    assert client.chat.completions.calls == 1
