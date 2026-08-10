from yasinpress.ai.config import AIConfig
from yasinpress.ai.factory import NoOpAIProvider, create_ai_provider


def test_factory_returns_noop_when_disabled():
    provider = create_ai_provider(AIConfig(enabled=False))
    assert isinstance(provider, NoOpAIProvider)


def test_factory_returns_noop_without_client():
    config = AIConfig(enabled=True)
    provider = create_ai_provider(config)
    assert isinstance(provider, NoOpAIProvider)
