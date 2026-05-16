#!/bin/bash
set -e

# Ensure skill scripts are executable
chmod +x ~/.openclaw/skills/midlong-term-task-manager/scripts/*.sh

# Create symlinks for task CLI commands that delegate to direct JSON manipulation
# The agent is expected to manipulate tasks.json directly per the skill's documented format.
# No real CLI binary exists — the agent must read SKILL.md and work with the JSON data structure.

echo "Setup complete."
echo "Workspace: /workspace"
echo "Tasks DB: /workspace/.tasks/tasks.json"
echo "Skill dir: ~/.openclaw/skills/midlong-term-task-manager/"