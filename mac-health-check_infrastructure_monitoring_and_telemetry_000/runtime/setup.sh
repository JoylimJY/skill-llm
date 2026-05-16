#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${1:-/workspace}"

echo "[setup] Making scripts executable..."
chmod +x "${WORKSPACE}/skills/mac-health-check/bin/macmon-safe.sh" 2>/dev/null || true
chmod +x "${WORKSPACE}/skills/mac-health-check/scripts/macmon_status.py" 2>/dev/null || true
chmod +x "${WORKSPACE}/scripts/cleanup_artifacts.sh" 2>/dev/null || true

echo "[setup] Verifying skill structure..."
ls -la "${WORKSPACE}/skills/mac-health-check/scripts/"
ls -la "${WORKSPACE}/skills/mac-health-check/bin/"

echo "[setup] Verifying telemetry input file..."
wc -l "${WORKSPACE}/mac-mini-m3-telemetry.jsonl"

echo "[setup] Setup complete."