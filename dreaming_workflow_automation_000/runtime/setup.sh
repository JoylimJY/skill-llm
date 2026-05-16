#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="/workspace"

# Ensure the dreaming script is executable
chmod +x "$WORKSPACE/skills/dreaming/scripts/should-dream.sh"
chmod +x "$WORKSPACE/skills/summarizer/scripts/summarize.sh" 2>/dev/null || true
chmod +x "$WORKSPACE/skills/planner/scripts/plan.sh" 2>/dev/null || true
chmod +x "$WORKSPACE/scripts/run-heartbeat.sh" 2>/dev/null || true

# Ensure required directories exist
mkdir -p "$WORKSPACE/data"
mkdir -p "$WORKSPACE/memory/dreams"

echo "Setup complete. Workspace ready at $WORKSPACE"

# Verify jq and python3 are available
jq --version
python3 --version