#!/usr/bin/env bash
set -e

# Ensure script is executable
chmod +x /workspace/scripts/script.sh

# Verify the script runs
cd /workspace
bash scripts/script.sh version > /dev/null 2>&1 && echo "[setup] script.sh is functional" || echo "[setup] WARNING: script.sh failed"

echo "[setup] Workspace ready."