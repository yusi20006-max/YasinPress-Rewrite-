from pathlib import Path


def test_runtime_and_dependency_sources_are_consistent():
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    requirements = Path("requirements.txt").read_text(encoding="utf-8")

    for dependency in ("PyYAML", "httpx", "feedparser"):
        assert dependency in pyproject
        assert dependency.lower() in requirements.lower()

    assert 'requires-python = ">=3.13"' in pyproject


def test_dev_dependencies_are_declared_in_project_metadata():
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    for dependency in ("pytest", "ruff", "mypy"):
        assert dependency in pyproject
