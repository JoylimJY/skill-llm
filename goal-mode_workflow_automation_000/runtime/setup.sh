#!/usr/bin/env bash
set -e

# Ensure workspace directories exist and have correct permissions
mkdir -p /home/ubuntu/.openclaw/workspace/goal-mode/references
mkdir -p /home/ubuntu/.openclaw/workspace/memory/goal-mode

chmod -R 755 /home/ubuntu/.openclaw/workspace

echo "Setup complete. Workspace ready at /home/ubuntu/.openclaw/workspace"
echo ""
echo "Task file: /home/ubuntu/.openclaw/workspace/task_input.json"
echo ""
echo "Directory tree:"
find /home/ubuntu/.openclaw/workspace -type f | sort