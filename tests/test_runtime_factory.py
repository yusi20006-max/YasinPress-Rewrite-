import os

import pytest

from yasinpress.config.runtime import RuntimeConfig
from yasinpress.runtime_factory import build_runtime


def test_runtime_factory_uses_shared_database_and_persistent_jobs(tmp_path):
    cfg = RuntimeConfig(database_path=str(tmp_path / "press.db"), worker_interval_seconds=0.01)
    bundle = build_runtime(config=cfg)
    assert os.path.exists(cfg.database_path)
    assert bundle.application.repository is bundle.database.articles
    assert bundle.worker.store is bundle.database.jobs
    assert bundle.worker.retry.attempts == cfg.max_job_attempts
    bundle.close()


def test_runtime_config_defaults_to_five_per_source():
    cfg = RuntimeConfig()
    assert cfg.max_publications_per_hour == 10
    assert cfg.max_source_publications_per_hour == 5
    cfg.validate()


def test_runtime_config_from_env(monkeypatch):
    monkeypatch.setenv("YASINPRESS_MAX_JOB_ATTEMPTS", "5")
    monkeypatch.setenv("YASINPRESS_MAX_PUBLICATIONS_PER_HOUR", "12")
    monkeypatch.setenv("YASINPRESS_MAX_SOURCE_PUBLICATIONS_PER_HOUR", "7")
    cfg = RuntimeConfig.from_env()
    assert cfg.max_job_attempts == 5
    assert cfg.max_publications_per_hour == 12
    assert cfg.max_source_publications_per_hour == 7
    cfg.validate()


def test_runtime_config_rejects_invalid_source_limit():
    cfg = RuntimeConfig(max_source_publications_per_hour=0)
    with pytest.raises(ValueError, match="max_source_publications_per_hour must be >= 1"):
        cfg.validate()


def test_runtime_factory_wires_source_limit(monkeypatch, tmp_path):
    captured = {}

    class FakePublicationQueueProcessor:
        def __init__(self, *, repositories, publishers, max_global_per_hour, max_source_per_hour, **kwargs):
            captured.update(
                repositories=repositories,
                publishers=publishers,
                max_global_per_hour=max_global_per_hour,
                max_source_per_hour=max_source_per_hour,
                extra=kwargs,
            )

        def process_cycle(self):
            return []

    monkeypatch.setattr(
        "yasinpress.publishing.queue_processor.PublicationQueueProcessor",
        FakePublicationQueueProcessor,
    )
    cfg = RuntimeConfig(
        database_path=str(tmp_path / "press.db"),
        max_publications_per_hour=12,
        max_source_publications_per_hour=7,
    )

    bundle = build_runtime(config=cfg, publishers=())
    try:
        assert captured["max_global_per_hour"] == 12
        assert captured["max_source_per_hour"] == 7
    finally:
        bundle.close()
