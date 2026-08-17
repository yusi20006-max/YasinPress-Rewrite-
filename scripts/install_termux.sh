#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
if [[ "${PREFIX}" != "/data/data/com.termux/files/usr" ]]; then
  echo "ERROR: this installer is for Termux only." >&2
  exit 1
fi

PYTHON_BIN="${PREFIX}/bin/python"
YASIN_AI_DIR="${HOME}/yasineco/Yasin-AI"

pkg update -y
pkg upgrade -y
# Use Termux-native Ruff. Installing ruff from PyPI on Android can trigger a
# large Rust/maturin source build instead of using a compatible wheel.
pkg install -y python git clang make pkg-config openssl openssl-tool libffi cmake patchelf ruff

"${PYTHON_BIN}" --version
ruff --version
rm -rf .venv
"${PYTHON_BIN}" -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel

# Yasin-AI is a canonical local Termux component. Install it from GitHub
# instead of resolving it through a generic package index.
if [[ ! -f "${YASIN_AI_DIR}/pyproject.toml" ]]; then
  mkdir -p "$(dirname "${YASIN_AI_DIR}")"
  git clone --depth 1 --branch main https://github.com/yusi20006-max/Yasin-AI.git "${YASIN_AI_DIR}"
fi
python -m pip install -e "${YASIN_AI_DIR}"
# Install only the test runner needed by the Termux validation. Do not install
# the full [dev] extra because it pulls ruff from PyPI and attempts a native
# Rust build on Android.
python -m pip install "pytest>=8.2,<10"

if [[ ! -f .env ]]; then
  cp .env.example .env
  chmod 600 .env || true
fi

python - <<'PY'
import sys
import yasinpress
import yasinai
print(f"Python: {sys.version}")
print(f"YasinPress: {yasinpress.__version__}")
print(f"Yasin-AI: {getattr(yasinai, '__version__', 'unknown')}")
print("YasinPress import: OK")
print("Yasin-AI public contracts: OK")
PY

python -m compileall -q yasinpress tests
python -m pytest -q
ruff check .
python -m yasinpress.cli.main --help

echo "YasinPress Termux installation completed successfully."
echo "Activate: source .venv/bin/activate"
echo "Configure: nano .env"
echo "CLI: yasinpress --help"
echo "Run: yasinpress run"
