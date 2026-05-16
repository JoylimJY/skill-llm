#!/usr/bin/env bash
set -euo pipefail

echo "[setup] Ensuring gc_and_checkpoint.sh is executable..."
chmod +x /workspace/skills/context-budgeting/scripts/gc_and_checkpoint.sh

echo "[setup] Verifying workspace structure..."
ls /workspace/skills/context-budgeting/scripts/
ls /workspace/memory/hot/

echo "[setup] Setup complete."