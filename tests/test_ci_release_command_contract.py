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


RELEASE_STATUS = Path("docs/RELEASE_STATUS.md")
RELEASE_EVIDENCE = Path("docs/PRODUCTION_CERTIFICATION_EVIDENCE.md")


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


def test_release_status_references_all_merged_release_hardening():
    status = RELEASE_STATUS.read_text(encoding="utf-8")
    assert "PR #154" in status
    assert "PR #156" in status
    assert "PR #158" in status
    assert "HARDEN-13" in status
    assert "**GREEN**" in status
    assert "production certification" in status.lower()


def test_release_status_keeps_operational_gate_separate():
    status = RELEASE_STATUS.read_text(encoding="utf-8").lower()
    evidence = RELEASE_EVIDENCE.read_text(encoding="utf-8").lower()

    assert "final / green" in status
    assert "manual production gate" in status
    assert "manual eitaa smoke-test result" in status
    assert "credential values must never be exposed" in status
    assert "never calls an external publisher" in evidence


def test_release_status_does_not_claim_final_green_without_operational_result():
    status = RELEASE_STATUS.read_text(encoding="utf-8")
    decision = next(
        line for line in status.splitlines() if line.startswith("**Decision:**")
    )
    assert "production certification pending" in decision
    assert "FINAL / GREEN" in status
    assert "remaining functional release blocker is operational production certification" in status
