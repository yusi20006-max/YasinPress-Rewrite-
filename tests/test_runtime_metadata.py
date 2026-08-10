from pathlib import Path


def test_runtime_metadata_matches_release_policy():
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    assert 'requires-python = ">=3.13"' in pyproject
    assert 'version = "1.0.0"' in pyproject
