#!/usr/bin/env bash
set -e

# Ensure the workspace task file is readable
chmod 644 /workspace/task.md
chmod -R 644 /workspace/ops/ 2>/dev/null || true
chmod -R 755 /workspace/ops/ 2>/dev/null || true

# The ~/brief directory should NOT pre-exist — the agent must create it per SKILL.md instructions
# Confirm it does not exist
if [ -d "$HOME/brief" ]; then
    rm -rf "$HOME/brief"
    echo "Cleaned up pre-existing ~/brief directory"
fi

echo "Setup complete. Workspace ready."
echo "Agent task file: /workspace/task.md"