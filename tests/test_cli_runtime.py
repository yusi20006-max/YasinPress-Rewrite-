from yasinpress.cli.main import main


def test_cli_config(monkeypatch):
    monkeypatch.setenv("YASINPRESS_DATABASE", ":memory:")
    assert main(["config"]) == 0


def test_cli_health(tmp_path, monkeypatch):
    monkeypatch.setenv("YASINPRESS_DATABASE", str(tmp_path / "health.db"))
    assert main(["health"]) == 0
