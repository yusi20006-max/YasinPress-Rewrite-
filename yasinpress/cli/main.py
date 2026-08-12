"""Command-line entrypoint."""

from __future__ import annotations

import argparse
import getpass
import os

from yasinpress.config.runtime import RuntimeConfig
from yasinpress.health import check_database
from yasinpress.runtime_factory import build_runtime
from yasinpress.sources.catalog import RSSFeed, active_feeds, probe_feed


def _startup_channel_setup() -> None:
    """Ask whether an Eitaa channel should be configured at startup."""
    existing_token = os.getenv("YASINPRESS_EITAA_TOKEN", "").strip()
    existing_channel = os.getenv("YASINPRESS_EITAA_CHANNEL", "").strip()

    try:
        answer = input("آیا کانالی برای اضافه کردن دارید؟ [y/N]: ").strip().lower()
    except EOFError:
        answer = ""

    if answer not in {"y", "yes"}:
        if existing_token and existing_channel:
            print(f"Eitaa channel active: {existing_channel}")
        else:
            print("No Eitaa channel added. Continuing with RSS feeds.")
        return

    try:
        token = getpass.getpass("Eitaa Token: ").strip()
        channel = input("Eitaa Channel: ").strip()
    except (EOFError, KeyboardInterrupt):
        token = channel = ""

    if token and channel:
        os.environ["YASINPRESS_EITAA_TOKEN"] = token
        os.environ["YASINPRESS_EITAA_CHANNEL"] = channel
        print(f"Eitaa channel configured: {channel}")
    elif existing_token and existing_channel:
        print(f"Keeping existing Eitaa channel: {existing_channel}")
    else:
        print("Eitaa channel configuration skipped: token and channel are both required.")


def _startup_feed_setup() -> None:
    """Validate configured RSS feeds and discover live alternatives when needed."""
    configured = tuple(
        url.strip() for url in os.getenv("YASINPRESS_FEEDS", "").split(",") if url.strip()
    )
    if configured:
        valid = tuple(
            feed
            for feed in (
                probe_feed(RSSFeed(f"Configured RSS {i}", url))
                for i, url in enumerate(configured, 1)
            )
            if feed is not None
        )
        if valid:
            print("RSS feeds active:")
            for feed in valid:
                print(f"  ✓ {feed.url}")
            os.environ["YASINPRESS_FEEDS"] = ",".join(feed.url for feed in valid)
            print(f"Starting with {len(valid)} RSS feed(s).")
            return
        print("Configured RSS feeds are not responding. Discovering active feeds...")

    try:
        feeds = active_feeds()
    except Exception as exc:  # noqa: BLE001 - active_feeds is a threadpool boundary that could throw any network/parsing exception
        print(f"RSS discovery failed: {exc}")
        return

    if not feeds:
        print("No active RSS feeds were detected.")
        return

    print("Active RSS feeds:")
    for index, feed in enumerate(feeds, 1):
        print(f"  {index}. {feed.name} — {feed.url}")

    try:
        answer = input("آیا فید سفارشی برای اضافه کردن دارید؟ [y/N]: ").strip().lower()
    except EOFError:
        answer = ""

    feed_urls = [feed.url for feed in feeds]
    if answer in {"y", "yes"}:
        try:
            custom_url = input("آدرس فید سفارشی: ").strip()
            if custom_url:
                feed_urls.append(custom_url)
        except EOFError:
            pass

    os.environ["YASINPRESS_FEEDS"] = ",".join(feed_urls)
    print(f"Starting with {len(feed_urls)} RSS feed(s).")


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
        _startup_channel_setup()
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
