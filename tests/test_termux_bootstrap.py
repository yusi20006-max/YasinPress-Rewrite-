from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "install_termux.sh"
PYPROJECT = ROOT / "pyproject.toml"


def test_termux_installer_is_fail_fast_and_bootstraps_canonical_ai() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert "set -euo pipefail" in text
    assert '"${PREFIX}" != "/data/data/com.termux/files/usr"' in text
    assert "pkg install -y python git clang make pkg-config openssl openssl-tool libffi cmake patchelf" in text
    assert '"${PYTHON_BIN}" -m venv .venv' in text
    assert 'git clone --depth 1 --branch main https://github.com/yusi20006-max/Yasin-AI.git' in text
    assert 'python -m pip install -e "${YASIN_AI_DIR}"' in text
    assert 'python -m pip install -e ".[dev]"' in text
    assert "cp .env.example .env" in text
    assert "python -m pytest -q" in text
    assert "python -m ruff check ." in text
    assert "python -m yasinpress.cli.main --help" in text


def test_yasin_ai_is_not_a_generic_yasinpress_dependency() -> None:
    text = PYPROJECT.read_text(encoding="utf-8")
    assert "yasinai @ git+" not in text
    assert '"yasinai' not in text
