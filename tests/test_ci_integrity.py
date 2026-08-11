from pathlib import Path


def test_ci_is_release_gate_not_a_compatibility_matrix():
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "workflow_dispatch:" in workflow
    assert 'python-version: "3.13"' in workflow
    assert 'python -m pip install -e ".[dev]"' in workflow
    assert "python -m compileall -q yasinpress tests" in workflow
    assert "python -m pytest -q" in workflow
    assert "python -m ruff check ." in workflow


def test_build_backend_is_setuptools():
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    assert 'build-backend = "setuptools.build_meta"' in pyproject
    assert "setuptools>=69" in pyproject
