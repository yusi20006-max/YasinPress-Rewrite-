#!/usr/bin/env python3
"""Credential-safe production certification preflight for the Termux target."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

SCHEMA_VERSION = 1
SECRET_ENV_VARS = (
    "YASINPRESS_SECRET_KEY",
    "YASINPRESS_EITAA_TOKEN",
    "OPENAI_API_KEY",
)
SERVICE_NAMES = ("hermes-agent", "yasin-ai", "yasinpress", "yasinrelay")


def command_output(command: list[str]) -> str | None:
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return (result.stdout or result.stderr).strip() or None


def package_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def git_commit() -> str | None:
    value = command_output(["git", "rev-parse", "HEAD"])
    return value if value and len(value) == 40 else None


def service_status(service: str) -> dict[str, str | bool | None]:
    sv = shutil.which("sv")
    if not sv:
        return {"available": False, "running": False, "status": None}

    output = command_output([sv, "status", service])
    if output is None:
        return {"available": True, "running": False, "status": None}

    return {
        "available": True,
        "running": output.startswith("run:"),
        "status": output,
    }


def build_report(check_services: bool = True) -> dict[str, object]:
    credentials = {
        name: {"configured": bool(os.environ.get(name))} for name in SECRET_ENV_VARS
    }
    services = (
        {name: service_status(name) for name in SERVICE_NAMES}
        if check_services
        else {}
    )

    checks = {
        "git_commit": git_commit(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "termux": bool(os.environ.get("PREFIX")) and "/com.termux/" in os.environ.get("PREFIX", ""),
        "yasinpress_version": package_version("yasinpress-rewrite"),
        "ruff_version": command_output(["ruff", "--version"]),
    }

    service_ready = all(item.get("running") for item in services.values()) if services else True
    repository_ready = bool(checks["git_commit"] and checks["yasinpress_version"])

    return {
        "schema_version": SCHEMA_VERSION,
        "mode": "preflight-only",
        "live_publisher_invoked": False,
        "checks": checks,
        "credentials": credentials,
        "services": services,
        "ready_for_manual_operational_gate": repository_ready and service_ready,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument(
        "--no-services",
        action="store_true",
        help="skip runit service checks; useful for repository-only verification",
    )
    args = parser.parse_args()

    report = build_report(check_services=not args.no_services)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"schema_version: {report['schema_version']}")
        print(f"mode: {report['mode']}")
        print(f"live_publisher_invoked: {report['live_publisher_invoked']}")
        print(f"ready_for_manual_operational_gate: {report['ready_for_manual_operational_gate']}")
        print(json.dumps(report["checks"], ensure_ascii=False, indent=2, sort_keys=True))
        print(json.dumps(report["credentials"], ensure_ascii=False, indent=2, sort_keys=True))
        print(json.dumps(report["services"], ensure_ascii=False, indent=2, sort_keys=True))

    return 0 if report["ready_for_manual_operational_gate"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
