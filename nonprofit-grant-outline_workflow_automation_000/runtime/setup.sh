#!/usr/bin/env bash
set -euo pipefail

# Make run.py executable
chmod +x /workspace/skills/nonprofit-grant-outline/scripts/run.py

echo "[setup] Skill scripts are ready."
echo "[setup] Workspace layout:"
find /workspace -maxdepth 4 -not -path '*/__pycache__/*' | sort