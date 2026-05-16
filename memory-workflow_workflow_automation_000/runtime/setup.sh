#!/bin/bash
set -e

WORKSPACE="/root/.openclaw/workspace"

# Ensure scripts are executable
chmod +x "$WORKSPACE/skills/memory-workflow/scripts/install.sh"
chmod +x "$WORKSPACE/skills/memory-workflow/scripts/daily-summary.sh"
chmod +x "$WORKSPACE/skills/memory-workflow/scripts/weekly-review.sh"

# Create logs directory
mkdir -p "$WORKSPACE/logs"
mkdir -p "$WORKSPACE/memory"

# Start cron daemon so cron-related installs work
service cron start 2>/dev/null || true

echo "Setup complete. Workspace ready."
echo "WORKSPACE=$WORKSPACE"
ls -la "$WORKSPACE/"