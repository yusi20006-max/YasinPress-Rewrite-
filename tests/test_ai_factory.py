from yasinpress.ai.config import AIConfig
from yasinpress.ai.factory import NoOpAIProvider, create_ai_provider
from yasinpress.ai.resilient import ResilientAIProvider


class FakeCompletions:
    def create(self, **_kwargs):
        return type("Response", (), {"choices": [type("Choice", (), {"message": type("Message", (), {"content": "rewritten"})()})()]})()


class FakeClient:
    chat = type("Chat", (), {"completions": FakeCompletions()})()


def test_factory_returns_noop_when_disabled():
    provider = create_ai_provider(AIConfig(enabled=False))
    assert isinstance(provider, NoOpAIProvider)


def test_factory_returns_noop_without_client():
    config = AIConfig(enabled=True)
    provider = create_ai_provider(config)
    assert isinstance(provider, NoOpAIProvider)


def test_factory_applies_configured_resilience_policy(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    config = AIConfig(enabled=True, timeout_seconds=7.5, model="test-model")
    provider = create_ai_provider(config, client=FakeClient())
    assert isinstance(provider, ResilientAIProvider)
    assert provider.policy.timeout_seconds == 7.5
    assert provider.policy.max_attempts == 2
