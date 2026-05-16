#!/usr/bin/env bash
set -e

# Make the run.py script executable
chmod +x /workspace/skills/deck-narrative-planner/scripts/run.py

echo "Setup complete. Skill scripts are executable."
echo ""
echo "Workspace structure:"
find /workspace -type f | sort