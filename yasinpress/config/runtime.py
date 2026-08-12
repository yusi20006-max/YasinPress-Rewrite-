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
    pwa_output_path: str = "data/pwa/feed.json"
    pwa_title: str = "YasinPress"
    pwa_home_page_url: str = ""
    pwa_feed_url: str = ""
    rss_output_path: str = "data/rss/feed.xml"
    rss_title: str = "YasinPress"
    rss_link: str = ""
    rss_feed_url: str = ""
    max_feed_items: int = 100
    max_article_age_hours: float = 12.0
    max_publications_per_hour: int = 10

    @classmethod
    def from_env(cls) -> RuntimeConfig:
        raw_feeds = os.getenv("YASINPRESS_FEEDS", "")
        feeds = tuple(url.strip() for url in raw_feeds.split(",") if url.strip())
        return cls(
            database_path=os.getenv("YASINPRESS_DATABASE", cls.database_path),
            worker_interval_seconds=float(os.getenv("YASINPRESS_WORKER_INTERVAL", cls.worker_interval_seconds)),
            scheduler_interval_seconds=float(os.getenv("YASINPRESS_SCHEDULER_INTERVAL", cls.scheduler_interval_seconds)),
            max_job_attempts=int(os.getenv("YASINPRESS_MAX_JOB_ATTEMPTS", cls.max_job_attempts)),
            request_timeout_seconds=float(os.getenv("YASINPRESS_REQUEST_TIMEOUT", cls.request_timeout_seconds)),
            feed_urls=feeds,
            feed_source=os.getenv("YASINPRESS_FEED_SOURCE", cls.feed_source),
            eitaa_token=os.getenv("YASINPRESS_EITAA_TOKEN", "").strip(),
            eitaa_channel=os.getenv("YASINPRESS_EITAA_CHANNEL", "").strip(),
            eitaa_api_base=os.getenv("YASINPRESS_EITAA_API_BASE", cls.eitaa_api_base).strip(),
            pwa_output_path=os.getenv("YASINPRESS_PWA_OUTPUT", cls.pwa_output_path).strip(),
            pwa_title=os.getenv("YASINPRESS_PWA_TITLE", cls.pwa_title).strip(),
            pwa_home_page_url=os.getenv("YASINPRESS_PWA_HOME_URL", cls.pwa_home_page_url).strip(),
            pwa_feed_url=os.getenv("YASINPRESS_PWA_FEED_URL", cls.pwa_feed_url).strip(),
            rss_output_path=os.getenv("YASINPRESS_RSS_OUTPUT", cls.rss_output_path).strip(),
            rss_title=os.getenv("YASINPRESS_RSS_TITLE", cls.rss_title).strip(),
            rss_link=os.getenv("YASINPRESS_RSS_LINK", cls.rss_link).strip(),
            rss_feed_url=os.getenv("YASINPRESS_RSS_FEED_URL", cls.rss_feed_url).strip(),
            max_feed_items=int(os.getenv("YASINPRESS_MAX_FEED_ITEMS", cls.max_feed_items)),
            max_article_age_hours=float(os.getenv("YASINPRESS_MAX_ARTICLE_AGE_HOURS", cls.max_article_age_hours)),
            max_publications_per_hour=int(os.getenv("YASINPRESS_MAX_PUBLICATIONS_PER_HOUR", cls.max_publications_per_hour)),
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
        if self.max_feed_items < 1:
            raise ValueError("max_feed_items must be >= 1")
        if not self.feed_source:
            raise ValueError("feed_source must not be empty")
        if not self.pwa_output_path or not self.rss_output_path:
            raise ValueError("PWA and RSS output paths must not be empty")
        if bool(self.eitaa_token) != bool(self.eitaa_channel):
            raise ValueError("YASINPRESS_EITAA_TOKEN and YASINPRESS_EITAA_CHANNEL must be set together")
        if not self.eitaa_api_base:
            raise ValueError("eitaa_api_base must not be empty")
