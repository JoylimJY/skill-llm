#!/usr/bin/env bash
set -e

# task_skill.py is already present in the workspace per the SKILL.md assumption.
# Ensure it is executable.
chmod +x /workspace/task_skill.py 2>/dev/null || true

# Make migration/backup scripts executable (distractors)
chmod +x /workspace/scripts/migration/run_migration.sh 2>/dev/null || true
chmod +x /workspace/scripts/backup/backup_db.sh 2>/dev/null || true

echo "Setup complete."