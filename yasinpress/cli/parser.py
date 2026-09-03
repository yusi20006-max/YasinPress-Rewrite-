"""CLI parser."""

import argparse


def build_parser() -> argparse.ArgumentParser:
    """Build command parser."""
    parser = argparse.ArgumentParser(prog="yasinpress")
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="Show version and exit.",
    )
    parser.add_argument(
        "command",
        choices=["status", "version", "config", "health", "run"],
        nargs="?",
        default="status",
    )
    return parser
