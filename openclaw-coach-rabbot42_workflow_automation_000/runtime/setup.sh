#!/bin/bash
set -e

WORKSPACE="${WORKSPACE:-/workspace}"

# Make all scripts executable
chmod +x "$WORKSPACE/scripts/sync-docs.sh"
chmod +x "$WORKSPACE/scripts/pick-daily-tip.sh"
chmod +x "$WORKSPACE/scripts/send-daily-tip.sh"
chmod +x "$WORKSPACE/tools/legacy/old-sync.sh"

echo "[setup] Scripts marked executable."
echo "[setup] Workspace ready at $WORKSPACE"
echo "[setup] Current structure:"
find "$WORKSPACE" -maxdepth 4 | sort