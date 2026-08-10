import os

from yasinpress.ai.config import AIConfig


def test_ai_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("YASINPRESS_AI_ENABLED", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    config = AIConfig.from_env()
    assert not config.enabled
    assert not config.usable()


def test_ai_config_reads_environment(monkeypatch):
    monkeypatch.setenv("YASINPRESS_AI_ENABLED", "true")
    monkeypatch.setenv("YASINPRESS_AI_BASE_URL", "https://relay.example/v1")
    monkeypatch.setenv("YASINPRESS_AI_MODEL", "test-model")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    config = AIConfig.from_env()
    assert config.usable()
    assert config.base_url == "https://relay.example/v1"
    assert config.model == "test-model"
    assert config.api_key == "test-key"
