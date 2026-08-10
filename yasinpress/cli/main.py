"""Command-line entrypoint."""
from __future__ import annotations

import argparse

from yasinpress.config.runtime import RuntimeConfig
from yasinpress.health import check_database
from yasinpress.runtime_factory import build_runtime


def main(argv: list[str] | None = None) -> int:
    """Run a YasinPress CLI command."""
    parser = argparse.ArgumentParser(prog="yasinpress")
    parser.add_argument("command", choices=["status", "version", "config", "health", "run"], nargs="?", default="status")
    args = parser.parse_args(argv)

    if args.command == "version":
        from yasinpress import __version__
        print(__version__)
        return 0
    if args.command == "config":
        RuntimeConfig.from_env().validate()
        print("configuration: ok")
        return 0

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
