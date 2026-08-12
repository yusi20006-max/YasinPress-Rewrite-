from datetime import UTC, datetime

from yasinpress.database.models import Article


def test_article_ai_failure_contract_preserves_provenance():
    article = Article(
        id="a1",
        title="Original title",
        url="https://example.test/a1",
        content="Original content",
        source="example",
        published_at=datetime(2026, 1, 1, tzinfo=UTC),
        ai_modified=False,
        ai_state="failed",
        ai_error="provider timeout",
        lifecycle_state="processed",
    )

    assert article.ai_modified is False
    assert article.ai_state == "failed"
    assert article.ai_error == "provider timeout"
    assert article.title == "Original title"
    assert article.content == "Original content"
