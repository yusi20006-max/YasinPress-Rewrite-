"""Repository-only scan for obvious hard-coded credential material."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

SKIP_PATHS = {
    Path("scripts/secret_exposure_scan.py"),
    Path("tests/test_secret_exposure_scan.py"),
}
PATTERNS = (
    ("private_key", re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")),
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("github_token", re.compile(r"\b(?:ghp|gho|ghs|github_pat)_[A-Za-z0-9_]{20,}\b")),
    ("telegram_bot_token", re.compile(r"\b\d{8,12}:[A-Za-z0-9_-]{30,}\b")),
    (
        "bearer_token",
        re.compile(
            r"\bAuthorization\s*:\s*Bearer\s+[A-Za-z0-9._-]{20,}",
            re.IGNORECASE,
        ),
    ),
    (
        "eitaa_token_assignment",
        re.compile(
            r"\bYASINPRESS_EITAA_TOKEN\s*=\s*(?!['\"]?\s*(?:$|#|\$\{|<|change-me))"
            r"['\"]?[A-Za-z0-9._-]{20,}['\"]?",
            re.IGNORECASE,
        ),
    ),
    (
        "generic_api_key_assignment",
        re.compile(
            r"\b(?:api[_-]?key|secret[_-]?key|access[_-]?token)\s*[:=]\s*"
            r"['\"]?[A-Za-z0-9._-]{24,}['\"]?",
            re.IGNORECASE,
        ),
    ),
)


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    return [Path(item) for item in result.stdout.decode().split("\0") if item]


def scan_file(path: Path) -> list[dict[str, object]]:
    if path in SKIP_PATHS or not path.is_file():
        return []

    try:
        data = path.read_bytes()
        if b"\0" in data:
            return []
        text = data.decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    findings = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for name, pattern in PATTERNS:
            if pattern.search(line):
                findings.append({"path": str(path), "line": line_number, "kind": name})
    return findings


def scan_repository() -> list[dict[str, object]]:
    findings = []
    for path in tracked_files():
        findings.extend(scan_file(path))
    return findings


def main() -> int:
    findings = scan_repository()
    if findings:
        for finding in findings:
            print(
                f"SECRET EXPOSURE: {finding['kind']} "
                f"at {finding['path']}:{finding['line']}"
            )
        return 1

    print("Secret exposure scan: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
