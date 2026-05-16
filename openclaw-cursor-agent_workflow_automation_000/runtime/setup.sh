#!/usr/bin/env bash
set -e

# Ensure all stub scripts are executable
chmod +x /workspace/cursor-agent-system/scripts/*.sh

echo "Setup complete. Workspace ready for agent."
ls -la /workspace/
ls -la /workspace/cursor-agent-system/scripts/
echo "openclaw.json contents:"
cat /workspace/openclaw.json
echo ""
echo "task_spec.json contents:"
cat /workspace/task_spec.json