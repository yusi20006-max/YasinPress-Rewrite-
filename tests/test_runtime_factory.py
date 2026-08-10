import os

from yasinpress.config.runtime import RuntimeConfig
from yasinpress.runtime_factory import build_runtime


def test_runtime_config_validation_and_factory(tmp_path):
    cfg = RuntimeConfig(database_path=str(tmp_path / "press.db"), worker_interval_seconds=0.01)
    bundle = build_runtime(config=cfg)
    assert os.path.exists(cfg.database_path)
    assert bundle.application.repository is bundle.database.articles
    bundle.close()


def test_runtime_config_from_env(monkeypatch):
    monkeypatch.setenv("YASINPRESS_MAX_JOB_ATTEMPTS", "5")
    cfg = RuntimeConfig.from_env()
    assert cfg.max_job_attempts == 5
    cfg.validate()
