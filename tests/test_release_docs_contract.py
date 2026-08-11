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
