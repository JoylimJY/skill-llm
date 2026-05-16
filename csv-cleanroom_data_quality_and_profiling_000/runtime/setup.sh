#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${WORKSPACE:-/workspace}"

# Make the bundled script executable
chmod +x "$WORKSPACE/skills/csv-cleanroom/scripts/csv_cleanroom.py"

echo "[setup] csv_cleanroom.py is executable."
echo "[setup] Workspace ready."