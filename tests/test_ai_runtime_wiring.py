import sys
import types

from yasinpress.ai.config import AIConfig
from yasinpress.ai.factory import create_ai_provider
from yasinpress.ai.openai_compatible import HTTPXOpenAICompatibleClient, OpenAICompatibleProvider
from yasinpress.ai.resilient import ResilientAIProvider
from yasinpress.runtime_factory import build_runtime


def test_factory_constructs_httpx_openai_compatible_client_without_injection(monkeypatch):
    monkeypatch.setenv("TEST_AI_KEY", "test-key")
    provider = create_ai_provider(
        AIConfig(
            enabled=True,
            provider="openai-compatible",
            base_url="https://relay.example/v1",
            model="test-model",
            api_key_env="TEST_AI_KEY",
        )
    )

    assert isinstance(provider, ResilientAIProvider)
    assert isinstance(provider.provider, OpenAICompatibleProvider)
    assert isinstance(provider.provider.client, HTTPXOpenAICompatibleClient)
    assert provider.provider.client.chat.completions.base_url == "https://relay.example/v1"


def test_runtime_builds_ai_from_environment_when_not_explicitly_injected(monkeypatch, tmp_path):
    package = types.ModuleType("yasinai")
    services = types.ModuleType("yasinai.services")

    class GenerationService:
        pass

    services.GenerationService = GenerationService
    package.services = services
    monkeypatch.setitem(sys.modules, "yasinai", package)
    monkeypatch.setitem(sys.modules, "yasinai.services", services)
    monkeypatch.setenv("YASINPRESS_AI_ENABLED", "true")
    monkeypatch.setenv("YASINPRESS_AI_PROVIDER", "yasin-ai")
    monkeypatch.setenv("YASINPRESS_AI_MODEL", "test-model")

    runtime = build_runtime(
        config=__import__("yasinpress.config.runtime", fromlist=["RuntimeConfig"]).RuntimeConfig(
            database_path=str(tmp_path / "runtime.db")
        )
    )
    try:
        assert isinstance(runtime.application.processing.ai, ResilientAIProvider)
        assert runtime.application.processing.ai.provider.model == "test-model"
    finally:
        runtime.close()


def test_runtime_preserves_explicit_ai_provider(monkeypatch, tmp_path):
    sentinel = object()
    runtime = build_runtime(
        config=__import__("yasinpress.config.runtime", fromlist=["RuntimeConfig"]).RuntimeConfig(
            database_path=str(tmp_path / "runtime.db")
        ),
        ai=sentinel,
    )
    try:
        assert runtime.application.processing.ai is sentinel
    finally:
        runtime.close()
