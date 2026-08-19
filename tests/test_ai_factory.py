import sys
import types

from yasinpress.ai.config import AIConfig
from yasinpress.ai.factory import NoOpAIProvider, create_ai_provider
from yasinpress.ai.resilient import ResilientAIProvider
from yasinpress.ai.yasin_ai import YasinAIProvider


def _install_fake_yasinai(monkeypatch):
    package = types.ModuleType("yasinai")
    services = types.ModuleType("yasinai.services")

    class GenerationService:
        def generate(self, _request):
            raise AssertionError("fake service must not be invoked by factory construction test")

    services.GenerationService = GenerationService
    package.services = services
    monkeypatch.setitem(sys.modules, "yasinai", package)
    monkeypatch.setitem(sys.modules, "yasinai.services", services)


def test_factory_returns_noop_when_disabled():
    provider = create_ai_provider(AIConfig(enabled=False))
    assert isinstance(provider, NoOpAIProvider)


def test_factory_selects_canonical_yasin_ai_provider(monkeypatch):
    _install_fake_yasinai(monkeypatch)
    provider = create_ai_provider(AIConfig(enabled=True, provider="yasin-ai", model="test-model"))
    assert isinstance(provider, ResilientAIProvider)
    assert isinstance(provider.provider, YasinAIProvider)
    assert provider.provider.model == "test-model"


def test_factory_keeps_legacy_openai_compatible_adapter_explicit():
    class FakeCompletions:
        def create(self, **_kwargs):
            return type("Response", (), {"choices": [type("Choice", (), {"message": type("Message", (), {"content": "rewritten"})()})()]})()

    class FakeClient:
        chat = type("Chat", (), {"completions": FakeCompletions()})()

    config = AIConfig(
        enabled=True,
        provider="openai-compatible",
        model="test-model",
        api_key_env="OPENAI_API_KEY",
    )
    import os
    os.environ["OPENAI_API_KEY"] = "test-key"
    try:
        provider = create_ai_provider(config, client=FakeClient())
        assert isinstance(provider, ResilientAIProvider)
        assert provider.provider.name == "openai-compatible"
    finally:
        os.environ.pop("OPENAI_API_KEY", None)
