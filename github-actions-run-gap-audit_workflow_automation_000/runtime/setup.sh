#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${WORKSPACE:-/workspace}"

echo "[setup] Verifying skill script exists..."
SCRIPT="$WORKSPACE/skills/github-actions-run-gap-audit/scripts/run-gap-audit.sh"
if [[ ! -f "$SCRIPT" ]]; then
  echo "[setup] ERROR: run-gap-audit.sh not found at $SCRIPT"
  exit 1
fi
chmod +x "$SCRIPT"
echo "[setup] Script is executable."

echo "[setup] Verifying artifact directory..."
ls "$WORKSPACE/artifacts/github-actions/" | head -5

echo "[setup] Setup complete."