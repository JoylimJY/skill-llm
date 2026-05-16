#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${1:-/workspace}"

echo "[setup] Making bingo script executable..."
chmod +x "$WORKSPACE/scripts/script.sh"

echo "[setup] Initializing bingo data directory..."
mkdir -p "$HOME/.local/share/bingo"

echo "[setup] Verifying script works..."
"$WORKSPACE/scripts/script.sh" new-game 2>&1 || true

echo "[setup] Done."