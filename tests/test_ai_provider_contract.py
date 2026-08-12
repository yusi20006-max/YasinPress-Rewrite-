import pytest

from yasinpress.ai import AIResult, DisabledAIProvider, FakeAIProvider


def test_disabled_provider_never_changes_article_content_contract():
    result = DisabledAIProvider().analyze("Title", "Content")
    assert result == AIResult(metadata={"provider": "disabled"})


def test_fake_provider_is_deterministic():
    expected = AIResult(
        title="Rewritten",
        summary="Summary",
        category="news",
        priority="important",
        breaking=True,
        metadata={"provider": "fake"},
    )
    assert FakeAIProvider(expected).analyze("Title", "Content") == expected


def test_fake_provider_can_model_failure_without_live_credentials():
    with pytest.raises(TimeoutError, match="timeout"):
        FakeAIProvider(error=TimeoutError("timeout")).analyze("Title", "Content")
