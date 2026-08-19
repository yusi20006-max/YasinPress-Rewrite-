from pathlib import Path


CANONICAL_COMMANDS = (
    "python -m compileall -q yasinpress tests",
    "python -m pytest -q",
    "ruff check .",
    "python -m yasinpress.cli.main --help",
)


def test_ci_contains_all_canonical_release_commands():
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert all(command in workflow for command in CANONICAL_COMMANDS)


def test_release_gate_documents_all_canonical_release_commands():
    gate = Path("docs/release-gate.md").read_text(encoding="utf-8")
    assert all(command in gate for command in CANONICAL_COMMANDS)


def test_ci_is_credential_free_and_external_publisher_free():
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8").lower()
    forbidden = ("eitaa_token", "eitaa api token", "publish_once", "publish_pending")
    assert not any(value in workflow for value in forbidden)
