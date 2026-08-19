import re
from pathlib import Path


def test_release_documentation_is_complete():
    required = [
        "docs/release-candidate.md",
        "docs/release-gate.md",
        "docs/FINAL_RELEASE_CHECKLIST.md",
        "docs/quality-gate.md",
        "docs/ci-compatibility.md",
        "docs/yasin-docs-alignment.md",
        "CHANGELOG.md",
    ]
    missing = [path for path in required if not Path(path).is_file()]
    assert not missing, f"Missing release documents: {missing}"


def test_release_docs_distinguish_repository_and_operational_certification():
    status = Path("docs/RELEASE_STATUS.md").read_text(encoding="utf-8")
    finalization = Path("docs/FINALIZATION.md").read_text(encoding="utf-8")
    readiness = Path("docs/release/RELEASE_READINESS.md").read_text(encoding="utf-8")
    gate = Path("docs/release-gate.md").read_text(encoding="utf-8")

    assert "operational production certification" in status.lower()
    assert "Repository code gate" in status
    assert "Operational production gate" in gate
    assert "repository code gate GREEN" in finalization
    assert "operational production certification pending" in readiness
    assert "fully production-certified" in gate


def test_release_docs_and_test_fixtures_do_not_contain_embedded_live_token_literals():
    candidates = list(Path("docs").rglob("*.md")) + list(Path("tests").rglob("*.py"))
    token_pattern = re.compile(
        r"(?:eitaa_token|eitaa[_-]?api[_-]?token)\s*=\s*['\"][A-Za-z0-9_-]{20,}['\"]",
        re.IGNORECASE,
    )
    offenders = []
    for path in candidates:
        text = path.read_text(encoding="utf-8")
        if token_pattern.search(text):
            offenders.append(str(path))
    assert not offenders, f"Embedded live-token literals found: {offenders}"
