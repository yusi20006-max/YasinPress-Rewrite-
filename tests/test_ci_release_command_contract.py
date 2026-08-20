from pathlib import Path

CANONICAL_COMMANDS = (
    "python -m compileall -q yasinpress tests",
    "python -m pytest -q",
    "ruff check .",
    "python -m yasinpress.cli.main --help",
)

WORKFLOW_DIR = Path(".github/workflows")
FORBIDDEN_WORKFLOW_TOKENS = (
    "${{ secrets.",
    "eitaa_token",
    "eitaa api token",
    "telegram_bot_token",
    "bot_token",
    "publish_once",
    "publish_pending",
    "send_message",
    "requests.post(",
    "httpx.post(",
    "curl -x post",
    "curl --request post",
    "yasinpress run",
    "python -m yasinpress.cli.main run",
)


def test_ci_contains_all_canonical_release_commands():
    workflow = (WORKFLOW_DIR / "ci.yml").read_text(encoding="utf-8")
    assert all(command in workflow for command in CANONICAL_COMMANDS)


def test_release_gate_documents_all_canonical_release_commands():
    gate = Path("docs/release-gate.md").read_text(encoding="utf-8")
    assert all(command in gate for command in CANONICAL_COMMANDS)


def test_all_workflows_are_credential_free_and_external_publisher_free():
    workflows = sorted(WORKFLOW_DIR.glob("*.y*ml"))
    assert workflows

    for path in workflows:
        content = path.read_text(encoding="utf-8").lower()
        assert "permissions:" in content, f"{path} must declare explicit permissions"
        assert "contents: write" not in content, f"{path} must not request write access"
        assert not any(token in content for token in FORBIDDEN_WORKFLOW_TOKENS), path


def test_ruff_workflow_is_non_mutating():
    workflow = (WORKFLOW_DIR / "ruff-autofix.yml").read_text(encoding="utf-8").lower()
    assert "contents: read" in workflow
    assert "git push" not in workflow
    assert "git commit" not in workflow
