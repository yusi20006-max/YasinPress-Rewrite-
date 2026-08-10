from pathlib import Path


def test_ci_targets_authoritative_runtime_and_runs_full_suite():
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert '"3.13"' in workflow
    assert "python -m compileall -q yasinpress tests" in workflow
    assert "python -m pytest -q" in workflow


def test_release_docs_exist():
    assert Path("docs/release-candidate.md").is_file()
    assert Path("docs/release-gate.md").is_file()
    assert Path("docs/ci-compatibility.md").is_file()
    assert Path("CHANGELOG.md").is_file()
