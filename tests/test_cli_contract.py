from yasinpress.cli.main import main


def test_cli_version(capsys):
    assert main(["version"]) == 0
    assert capsys.readouterr().out.strip() == "1.0.0"


def test_cli_version_flag(capsys):
    assert main(["--version"]) == 0
    assert capsys.readouterr().out.strip() == "1.0.0"


def test_cli_v_flag(capsys):
    assert main(["-v"]) == 0
    assert capsys.readouterr().out.strip() == "1.0.0"


def test_cli_status_smoke():
    result = main(["status"])
    assert result in (0, 1)
