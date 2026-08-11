from pathlib import Path


def test_package_metadata_and_entrypoint_are_declared():
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    assert 'name = "yasinpress-rewrite"' in pyproject
    assert 'version = "1.0.0"' in pyproject
    assert 'yasinpress = "yasinpress.cli.main:main"' in pyproject
    assert 'include = ["yasinpress*"]' in pyproject


def test_core_package_exists():
    package = Path("yasinpress")
    assert package.is_dir()
    assert (package / "__init__.py").is_file()
