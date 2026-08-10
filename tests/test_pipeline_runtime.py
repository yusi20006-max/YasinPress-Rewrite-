from datetime import UTC, datetime

from yasinpress.pipeline.runtime import ArticlePipeline
from yasinpress.sources.feed import FeedItem


def item(title: str = "News", content: str = "<b>Body</b>") -> FeedItem:
    return FeedItem(title, "https://example.com/news", content, datetime.now(UTC))


def test_pipeline_cleans_validates_and_processes():
    result = ArticlePipeline("test").process([item()])
    assert result.processed == 1
    assert result.rejected == 0
    assert result.articles[0].content == "Body"


def test_pipeline_rejects_invalid_url():
    result = ArticlePipeline("test").process([FeedItem("News", "not-a-url", "Body", datetime.now(UTC))])
    assert result.processed == 0
    assert result.rejected == 1


def test_pipeline_skips_duplicates():
    result = ArticlePipeline("test", duplicate=lambda _: True).process([item()])
    assert result.processed == 0
    assert result.rejected == 0
