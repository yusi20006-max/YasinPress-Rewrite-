import importlib.util
from pathlib import Path

SCRIPT = Path("scripts/production_certification_preflight.py")


def load_module():
    spec = importlib.util.spec_from_file_location(
        "production_certification_preflight", SCRIPT
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_preflight_schema_is_credential_safe(monkeypatch):
    module = load_module()
    monkeypatch.setenv("YASINPRESS_EITAA_TOKEN", "super-secret-token")
    monkeypatch.setenv("YASINPRESS_SECRET_KEY", "super-secret-key")

    report = module.build_report(check_services=False)

    assert report["schema_version"] == 1
    assert report["mode"] == "preflight-only"
    assert report["live_publisher_invoked"] is False
    assert report["credentials"]["YASINPRESS_EITAA_TOKEN"] == {"configured": True}
    assert report["credentials"]["YASINPRESS_SECRET_KEY"] == {"configured": True}
    assert "super-secret-token" not in str(report)
    assert "super-secret-key" not in str(report)


def test_preflight_does_not_require_credentials(monkeypatch):
    module = load_module()
    for name in module.SECRET_ENV_VARS:
        monkeypatch.delenv(name, raising=False)

    report = module.build_report(check_services=False)

    assert all(item["configured"] is False for item in report["credentials"].values())
    assert report["live_publisher_invoked"] is False


def test_service_check_is_supervisor_read_only(monkeypatch):
    module = load_module()
    calls = []

    monkeypatch.setattr(module.shutil, "which", lambda name: "/usr/bin/sv")

    def fake_output(command):
        calls.append(command)
        return "run: yasinpress: (pid 123) 10s"

    monkeypatch.setattr(module, "command_output", fake_output)
    result = module.service_status("yasinpress")

    assert result["available"] is True
    assert result["running"] is True
    assert calls == [["/usr/bin/sv", "status", "yasinpress"]]


def test_preflight_source_contains_no_secret_values():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "super-secret" not in source
    assert "requests.post(" not in source
    assert "httpx.post(" not in source
    assert "YASINPRESS_EITAA_TOKEN" in source
