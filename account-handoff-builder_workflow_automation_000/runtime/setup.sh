#!/usr/bin/env bash
set -e

# Default WORKSPACE if not set
WORKSPACE="${WORKSPACE:-/workspace}"

# Make the run.py script executable
chmod +x "$WORKSPACE/skills/account-handoff-builder/scripts/run.py"

echo "[setup] Skill scripts are ready."
echo "[setup] Workspace: $WORKSPACE"
ls -R "$WORKSPACE/skills/account-handoff-builder/"