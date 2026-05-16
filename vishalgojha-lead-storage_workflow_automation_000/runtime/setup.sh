#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_DIR="${WORKSPACE_DIR:-/workspace}"

echo "[setup] Ensuring storage directory exists and is writable..."
mkdir -p "$WORKSPACE_DIR/storage"
chmod 755 "$WORKSPACE_DIR/storage"

echo "[setup] Verifying schema files are present..."
ls "$WORKSPACE_DIR/references/"

echo "[setup] Setup complete."