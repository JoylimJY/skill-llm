#!/bin/bash
set -e

# Ensure ~/.local/bin exists (the skill standard requires symlinks there)
mkdir -p ~/.local/bin

# Make sure existing distractor scripts are executable
chmod +x /workspace/tools/bin/openclaw 2>/dev/null || true
chmod +x /workspace/skills/ssh-op/scripts/onboard.sh 2>/dev/null || true
chmod +x /workspace/skills/ssh-op/scripts/smoke-test.sh 2>/dev/null || true
chmod +x /workspace/skills/docker-manager/scripts/run.sh 2>/dev/null || true
chmod +x /workspace/skills/db-backup/scripts/run-backup.sh 2>/dev/null || true
chmod +x /workspace/skills/db-backup/scripts/onboard.sh 2>/dev/null || true

echo "Setup complete."