import os

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


def test_runtime_config_from_env(monkeypatch):
    monkeypatch.setenv("YASINPRESS_MAX_JOB_ATTEMPTS", "5")
    cfg = RuntimeConfig.from_env()
    assert cfg.max_job_attempts == 5
    cfg.validate()


def test_runtime_factory_wires_eitaa_publisher(tmp_path):
    cfg = RuntimeConfig(
        database_path=str(tmp_path / "press.db"),
        eitaa_bot_token="test-token",
        eitaa_channel="@test-channel",
    )
    bundle = build_runtime(config=cfg)
    assert len(bundle.application.processing.publisher.publishers) == 1
    publisher = bundle.application.processing.publisher.publishers[0].publisher
    assert publisher.name == "eitaa"
    assert publisher.channel == "@test-channel"
    bundle.close()
