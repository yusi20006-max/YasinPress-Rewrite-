from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeConfig:
    database_path: str = "yasinpress.db"
    worker_interval_seconds: float = 1.0
    scheduler_interval_seconds: float = 30.0
    max_job_attempts: int = 3
    request_timeout_seconds: float = 20.0
    feed_urls: tuple[str, ...] = ()
    feed_source: str = "rss"
    eitaa_bot_token: str = ""
    eitaa_channel: str = "@yasinpress"

    @classmethod
    def from_env(cls) -> RuntimeConfig:
        raw_feeds = os.getenv("YASINPRESS_FEEDS", "")
        feeds = tuple(url.strip() for url in raw_feeds.split(",") if url.strip())
        return cls(
            database_path=os.getenv(
                "YASINPRESS_DATABASE",
                os.getenv("YASINPRESS_DATABASE_PATH", cls.database_path),
            ),
            worker_interval_seconds=float(
                os.getenv("YASINPRESS_WORKER_INTERVAL", cls.worker_interval_seconds)
            ),
            scheduler_interval_seconds=float(
                os.getenv("YASINPRESS_SCHEDULER_INTERVAL", cls.scheduler_interval_seconds)
            ),
            max_job_attempts=int(os.getenv("YASINPRESS_MAX_JOB_ATTEMPTS", cls.max_job_attempts)),
            request_timeout_seconds=float(
                os.getenv("YASINPRESS_REQUEST_TIMEOUT", cls.request_timeout_seconds)
            ),
            feed_urls=feeds,
            feed_source=os.getenv("YASINPRESS_FEED_SOURCE", cls.feed_source),
            eitaa_bot_token=os.getenv(
                "EITAA_BOT_TOKEN",
                os.getenv("YASINPRESS_EITAA_BOT_TOKEN", ""),
            ).strip(),
            eitaa_channel=os.getenv(
                "EITAA_CHANNEL",
                os.getenv("YASINPRESS_EITAA_CHANNEL", cls.eitaa_channel),
            ).strip(),
        )

    def validate(self) -> None:
        if not self.database_path:
            raise ValueError("database_path must not be empty")
        if self.worker_interval_seconds <= 0 or self.scheduler_interval_seconds <= 0:
            raise ValueError("runtime intervals must be positive")
        if self.max_job_attempts < 1:
            raise ValueError("max_job_attempts must be >= 1")
        if self.request_timeout_seconds <= 0:
            raise ValueError("request_timeout_seconds must be positive")
        if not self.feed_source:
            raise ValueError("feed_source must not be empty")
        if self.eitaa_bot_token and not self.eitaa_channel:
            raise ValueError("eitaa_channel must not be empty when Eitaa publishing is enabled")
