"""Command-line entrypoint."""

from __future__ import annotations

import argparse
import os

from yasinpress.config.runtime import RuntimeConfig
from yasinpress.health import check_database
from yasinpress.runtime_factory import build_runtime
from yasinpress.sources.catalog import RSSFeed, active_feeds


def _startup_feed_setup() -> None:
    """Discover active RSS feeds when none are configured."""
    configured = tuple(
        url.strip() for url in os.getenv("YASINPRESS_FEEDS", "").split(",") if url.strip()
    )
    if configured:
        print("RSS feeds configured:")
        for url in configured:
            print(f"  - {url}")
        return

    try:
        answer = input("آیا RSS جدیدی برای اضافه کردن دارید؟ [y/N]: ").strip().lower()
    except EOFError:
        answer = ""

    try:
        feeds = active_feeds()
    except Exception as exc:
        print(f"RSS discovery failed: {exc}")
        return

    if not feeds:
        print("No active RSS feeds were detected.")
        return

    print("Active RSS feeds:")
    for index, feed in enumerate(feeds, 1):
        print(f"  {index}. {feed.name} — {feed.url}")

    selected = list(feeds)
    if answer in {"y", "yes"}:
        try:
            custom = input(
                "RSS URL(s), comma-separated (Enter to keep the active list): "
            ).strip()
        except EOFError:
            custom = ""
        if custom:
            selected.extend(
                RSSFeed(f"Custom RSS {index}", url.strip())
                for index, url in enumerate(custom.split(","), 1)
                if url.strip()
            )

    os.environ["YASINPRESS_FEEDS"] = ",".join(feed.url for feed in selected)
    print(f"Starting with {len(selected)} RSS feed(s).")


def main(argv: list[str] | None = None) -> int:
    """Run a YasinPress CLI command."""
    parser = argparse.ArgumentParser(prog="yasinpress")
    parser.add_argument(
        "command",
        choices=["status", "version", "config", "health", "run"],
        nargs="?",
        default="status",
    )
    args = parser.parse_args(argv)

    if args.command == "version":
        from yasinpress import __version__

        print(__version__)
        return 0
    if args.command == "config":
        RuntimeConfig.from_env().validate()
        print("configuration: ok")
        return 0

    if args.command == "run":
        _startup_feed_setup()

    bundle = build_runtime()
    try:
        if args.command in {"status", "health"}:
            result = check_database(bundle.database.connection)
            print(f"database: {'ok' if result.ok else 'error'}")
            return 0 if result.ok else 1
        bundle.runtime.run()
        return 0
    except KeyboardInterrupt:
        return 0
    finally:
        bundle.close()


if __name__ == "__main__":
    raise SystemExit(main())
