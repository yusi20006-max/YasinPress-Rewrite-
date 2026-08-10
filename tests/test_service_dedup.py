from datetime import datetime, timezone

from yasinpress.pipeline.service import ProcessingService
from yasinpress.sources.feed import FeedItem


def test_processing_service_deduplicates_before_pipeline():
    service = ProcessingService(source="rss")
    now = datetime.now(timezone.utc)
    items = [
        FeedItem("one", "https://example.com/1", "body", now),
        FeedItem("same article", "https://example.com/1", "changed", now),
    ]
    report = service.process(items)
    assert report.pipeline.processed == 1
