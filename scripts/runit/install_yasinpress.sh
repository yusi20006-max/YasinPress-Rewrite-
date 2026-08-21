#!/data/data/com.termux/files/usr/bin/sh
set -eu

REPO_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
SERVICE_DIR="${PREFIX:?}/var/service/yasinpress"
RUN_TEMPLATE="$REPO_ROOT/scripts/runit/yasinpress/run"

if [ ! -x "$REPO_ROOT/.venv/bin/yasinpress" ]; then
    echo "YasinPress virtualenv executable not found: $REPO_ROOT/.venv/bin/yasinpress" >&2
    echo "Create/install the project virtualenv first." >&2
    exit 1
fi

if [ ! -d "$PREFIX/var/service" ]; then
    echo "Termux runit service directory not found: $PREFIX/var/service" >&2
    exit 1
fi

mkdir -p "$SERVICE_DIR"

# Stop the current instance before replacing the service definition.
sv down "$SERVICE_DIR" 2>/dev/null || true
sleep 1

cp "$RUN_TEMPLATE" "$SERVICE_DIR/run"
chmod +x "$SERVICE_DIR/run"

# The current validated deployment intentionally has no nested svlogd logger.
rm -rf "$SERVICE_DIR/log"

sleep 1
sv up "$SERVICE_DIR"
sleep 2

sv status "$SERVICE_DIR"
