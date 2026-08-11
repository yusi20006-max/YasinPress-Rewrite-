from pathlib import Path

from yasinpress import __version__
from yasinpress.publishing import PublishResult, Publisher


def test_release_contract_is_available():
    assert __version__ == "1.0.0"
    assert Publisher is not None
    assert PublishResult is not None


def test_release_gate_files_exist():
    assert Path("docs/release-gate.md").is_file()
    assert Path("docs/release-candidate.md").is_file()
    assert Path("docs/FINAL_RELEASE_CHECKLIST.md").is_file()
    assert Path("CHANGELOG.md").is_file()


def test_runtime_metadata_is_authoritative():
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "1.0.0"' in pyproject
    assert 'requires-python = ">=3.13"' in pyproject
