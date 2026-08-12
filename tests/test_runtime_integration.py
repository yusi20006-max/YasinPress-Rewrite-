from datetime import timedelta

from yasinpress.config.runtime import RuntimeConfig
from yasinpress.runtime_factory import build_runtime


def test_runtime_bundle_wires_scheduler_and_persistent_publishing(tmp_path):
    cfg = RuntimeConfig(
        database_path=str(tmp_path / "press.db"),
        worker_interval_seconds=0.01,
        scheduler_interval_seconds=10.0,
        feed_urls=(),
    )
    bundle = build_runtime(config=cfg)
    assert bundle.scheduler.tasks == []
    assert bundle.database.delivery_history is not None
    assert bundle.database.idempotency is not None
    assert bundle.worker.store is bundle.database.jobs
    bundle.close()


def test_scheduler_task_is_registered_for_configured_feeds(tmp_path):
    cfg = RuntimeConfig(
        database_path=str(tmp_path / "press.db"),
        worker_interval_seconds=0.01,
        scheduler_interval_seconds=10.0,
        feed_urls=("https://example.com/feed.xml",),
    )
    bundle = build_runtime(config=cfg)
    assert len(bundle.scheduler.tasks) == 1
    assert bundle.scheduler.tasks[0].schedule.interval == timedelta(seconds=10)
    bundle.close()


def test_runtime_factory_exposes_persistent_queue_processor(tmp_path):
    cfg = RuntimeConfig(
        database_path=str(tmp_path / "press.db"),
        worker_interval_seconds=0.01,
        scheduler_interval_seconds=10.0,
        feed_urls=(),
        max_publications_per_hour=10,
    )
    bundle = build_runtime(config=cfg)
    try:
        assert bundle.application is not None
        assert bundle.runtime.watchdog is not None
        assert bundle.config.max_publications_per_hour == 10
    finally:
        bundle.close()
