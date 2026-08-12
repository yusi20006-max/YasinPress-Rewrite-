from yasinpress.ai.base import AIResult
from yasinpress.ai.resilient import AIResiliencePolicy, ResilientAIProvider


def test_resilient_ai_preserves_original_on_provider_failure():
    class FailingProvider:
        name = "test"

        def enrich(self, article):
            raise RuntimeError("provider down")

    provider = ResilientAIProvider(FailingProvider(), AIResiliencePolicy(timeout_seconds=1, max_attempts=2))
    result = provider.enrich(type("Article", (), {"title": "Original", "content": "Source"})())

    assert isinstance(result, AIResult)
    assert result.success is False
    assert result.title == "Original"
    assert result.content == "Source"


def test_priority_and_breaking_contracts_are_deterministic():
    from yasinpress.processing.breaking import detect_breaking
    from yasinpress.processing.priority import calculate_priority

    priority = calculate_priority("زلزله در تهران")
    breaking = detect_breaking("زلزله در تهران")
    assert priority.level == "urgent"
    assert breaking.is_breaking is False
