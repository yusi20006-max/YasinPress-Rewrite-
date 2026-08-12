from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeConfig:
    database_path: str = "yasinpress.db"
    worker_interval_seconds: float = 1.0
    scheduler_interval_seconds: float = 600.0
    max_job_attempts: int = 3
    request_timeout_seconds: float = 20.0
    feed_urls: tuple[str, ...] = ()
    feed_source: str = "rss"
    eitaa_token: str = ""
    eitaa_channel: str = ""
    eitaa_api_base: str = "https://eitaayar.ir/api"
    max_article_age_hours: float = 12.0
    max_publications_per_hour: int = 10

    @classmethod
    def from_env(cls) -> RuntimeConfig:
        raw_feeds = os.getenv("YASINPRESS_FEEDS", "")
        feeds = tuple(url.strip() for url in raw_feeds.split(",") if url.strip())
        return cls(
            database_path=os.getenv("YASINPRESS_DATABASE", cls.database_path),
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
            eitaa_token=os.getenv("YASINPRESS_EITAA_TOKEN", "").strip(),
            eitaa_channel=os.getenv("YASINPRESS_EITAA_CHANNEL", "").strip(),
            eitaa_api_base=os.getenv("YASINPRESS_EITAA_API_BASE", cls.eitaa_api_base).strip(),
            max_article_age_hours=float(
                os.getenv("YASINPRESS_MAX_ARTICLE_AGE_HOURS", cls.max_article_age_hours)
            ),
            max_publications_per_hour=int(
                os.getenv("YASINPRESS_MAX_PUBLICATIONS_PER_HOUR", cls.max_publications_per_hour)
            ),
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
        if self.max_article_age_hours <= 0:
            raise ValueError("max_article_age_hours must be positive")
        if self.max_publications_per_hour < 1:
            raise ValueError("max_publications_per_hour must be >= 1")
        if not self.feed_source:
            raise ValueError("feed_source must not be empty")
        if bool(self.eitaa_token) != bool(self.eitaa_channel):
            raise ValueError(
                "YASINPRESS_EITAA_TOKEN and YASINPRESS_EITAA_CHANNEL must be set together"
            )
        if not self.eitaa_api_base:
            raise ValueError("eitaa_api_base must not be empty")
