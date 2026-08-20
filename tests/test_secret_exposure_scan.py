import importlib.util
from pathlib import Path

SCRIPT = Path("scripts/secret_exposure_scan.py")


def load_module():
    spec = importlib.util.spec_from_file_location("secret_exposure_scan", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_safe_environment_examples_are_not_flagged(tmp_path):
    module = load_module()
    path = tmp_path / "safe.env.example"
    path.write_text(
        "YASINPRESS_EITAA_TOKEN=\n"
        "YASINPRESS_EITAA_TOKEN=${EITAA_TOKEN}\n"
        "YASINPRESS_EITAA_TOKEN=change-me\n"
        "OPENAI_API_KEY=OPENAI_API_KEY\n",
        encoding="utf-8",
    )

    assert module.scan_file(path) == []


def test_obvious_credentials_are_detected(tmp_path):
    module = load_module()
    path = tmp_path / "unsafe.txt"
    path.write_text(
        "OPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwxyz123456\n"
        "Authorization: Bearer abcdefghijklmnopqrstuvwxyz123456\n"
        "YASINPRESS_EITAA_TOKEN=abcdefghijklmnopqrstuvwxyz123456\n"
        "-----BEGIN PRIVATE KEY-----\n",
        encoding="utf-8",
    )

    findings = module.scan_file(path)
    assert {item["kind"] for item in findings} >= {
        "openai_key",
        "bearer_token",
        "eitaa_token_assignment",
        "private_key",
    }


def test_scanner_skips_its_own_detector_source():
    module = load_module()
    assert module.scan_file(Path("scripts/secret_exposure_scan.py")) == []
