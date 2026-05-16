#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${WORKSPACE:-/workspace}"

# Ensure the audit script is executable
SCRIPT_PATH="$WORKSPACE/skills/github-actions-manual-trigger-audit/scripts/manual-trigger-audit.sh"
if [ -f "$SCRIPT_PATH" ]; then
    chmod +x "$SCRIPT_PATH"
    echo "[setup] chmod +x $SCRIPT_PATH"
else
    echo "[setup] WARNING: audit script not found at $SCRIPT_PATH"
fi

echo "[setup] Workspace ready."