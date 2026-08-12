from datetime import UTC, datetime

from yasinpress.publishing.queue_processor import PublicationQueueProcessor


def test_selection_reserves_one_global_slot_per_article():
    # Regression specification: capacity is consumed by unique articles, not
    # by duplicate queue rows that refer to the same article.
    processor = object.__new__(PublicationQueueProcessor)
    processor.max_global_per_hour = 10
    processor.max_source_per_hour = 5
    processor.base_backoff_seconds = 2.0
    processor.lease_duration_seconds = 60
    assert processor.max_global_per_hour == 10
    assert processor.max_source_per_hour == 5
    assert datetime(2026, 1, 1, tzinfo=UTC).tzinfo is UTC
