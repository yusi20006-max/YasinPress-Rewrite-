"""Command-line entrypoint."""

from __future__ import annotations

import argparse
import getpass
import os
from pathlib import Path

from yasinpress.config.runtime import RuntimeConfig
from yasinpress.health import check_database
from yasinpress.runtime_factory import build_runtime
from yasinpress.sources.catalog import RSSFeed, active_feeds, probe_feed


def _startup_channel_setup() -> None:
    """Load and persist Eitaa credentials with blank-to-keep behavior."""
    env_file = Path(".env")

    def load_saved():
        values = {}
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if "=" in line and not line.lstrip().startswith("#"):
                    key, value = line.split("=", 1)
                    values[key.strip()] = value.strip().strip('"').strip("'")
        return values

    def save_saved(values):
        lines = env_file.read_text(encoding="utf-8").splitlines() if env_file.exists() else []
        keys = {
            "YASINPRESS_EITAA_TOKEN": values["YASINPRESS_EITAA_TOKEN"],
            "YASINPRESS_EITAA_CHANNEL": values["YASINPRESS_EITAA_CHANNEL"],
        }
        seen = set()
        output = []
        for line in lines:
            key = line.split("=", 1)[0].strip() if "=" in line else ""
            if key in keys:
                output.append(f"{key}={keys[key]}")
                seen.add(key)
            else:
                output.append(line)
        for key, value in keys.items():
            if key not in seen:
                output.append(f"{key}={value}")
        env_file.write_text("\n".join(output) + "\n", encoding="utf-8")
        try:
            env_file.chmod(0o600)
        except OSError:
            pass

    saved = load_saved()
    existing_token = os.getenv("YASINPRESS_EITAA_TOKEN", "").strip() or saved.get(
        "YASINPRESS_EITAA_TOKEN", ""
    )
    existing_channel = os.getenv("YASINPRESS_EITAA_CHANNEL", "").strip() or saved.get(
        "YASINPRESS_EITAA_CHANNEL", ""
    )

    try:
        token = getpass.getpass(
            "کد ایتا [Enter برای حفظ مقدار قبلی]: "
        ).strip()
        channel = input(
            "آدرس کانال [Enter برای حفظ مقدار قبلی]: "
        ).strip()
    except (EOFError, KeyboardInterrupt):
        token = channel = ""

    token = token or existing_token
    channel = channel or existing_channel

    if token and channel:
        os.environ["YASINPRESS_EITAA_TOKEN"] = token
        os.environ["YASINPRESS_EITAA_CHANNEL"] = channel
        save_saved({
            "YASINPRESS_EITAA_TOKEN": token,
            "YASINPRESS_EITAA_CHANNEL": channel,
        })
        print(f"Eitaa channel active: {channel}")
    else:
        print("Eitaa channel is not configured.")

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
    except Exception as exc:
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
