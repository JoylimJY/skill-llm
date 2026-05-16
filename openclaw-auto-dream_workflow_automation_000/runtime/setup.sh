#!/usr/bin/env bash
set -e

echo "[setup] Setting permissions on workspace..."
chmod -R 755 "${WORKSPACE_DIR:-/workspace}"

echo "[setup] Verifying workspace structure..."
ls "${WORKSPACE_DIR:-/workspace}/daily/" | head -10
ls "${WORKSPACE_DIR:-/workspace}/memory/"

echo "[setup] Setup complete."