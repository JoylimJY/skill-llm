#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_DIR="${WORKSPACE_DIR:-/workspace}"

echo "[setup] Making CLI tools executable..."
chmod +x "$WORKSPACE_DIR/skills/life-control/bin/lc"
chmod +x "$WORKSPACE_DIR/skills/life-control/bin/qlog"
chmod +x "$WORKSPACE_DIR/skills/life-control/scripts/bootstrap.sh"
chmod +x "$WORKSPACE_DIR/skills/life-control/scripts/setup-agents.sh"
chmod +x "$WORKSPACE_DIR/skills/life-control/scripts/telegram-sender.sh"
for f in "$WORKSPACE_DIR/skills/life-control/routines/"*.sh; do
    chmod +x "$f"
done

echo "[setup] Adding CLI tools to PATH..."
# Create symlinks in /usr/local/bin so `lc` and `qlog` work anywhere
ln -sf "$WORKSPACE_DIR/skills/life-control/bin/lc"   /usr/local/bin/lc
ln -sf "$WORKSPACE_DIR/skills/life-control/bin/qlog" /usr/local/bin/qlog

echo "[setup] Exporting LC_DB_PATH..."
echo "export LC_DB_PATH=$WORKSPACE_DIR/skills/life-control/db/life-control.db" \
    >> /etc/environment

echo "[setup] Ensuring log and db dirs exist..."
mkdir -p "$WORKSPACE_DIR/skills/life-control/db"
mkdir -p "$WORKSPACE_DIR/skills/life-control/logs"

echo "[setup] Done."