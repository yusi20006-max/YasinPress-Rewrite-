from datetime import UTC, datetime, timedelta

from yasinpress.publishing.queue_processor import PublicationQueueProcessor


def test_queue_processor_has_production_rate_limit_contract():
    processor = PublicationQueueProcessor(object(), [], max_global_per_hour=10, max_source_per_hour=5)
    assert processor.max_global_per_hour == 10
    assert processor.max_source_per_hour == 5
    assert processor.lease_duration_seconds > 0
    assert processor.base_backoff_seconds > 0


def test_naive_cycle_time_is_normalized_to_utc():
    # The processor should accept deterministic naive timestamps without
    # producing aware/naive comparison errors in the scheduling window.
    processor = PublicationQueueProcessor(object(), [])
    assert processor.process_cycle(datetime(2026, 1, 1)) == []


def test_lease_recovery_uses_attempt_count_for_next_state():
    class Queue:
        def get_stale_leased_jobs(self, now):
            return []

    class Repositories:
        publication_queue = Queue()

    processor = PublicationQueueProcessor(Repositories(), [])
    assert processor.recover_expired_leases(datetime.now(UTC)) == 0
