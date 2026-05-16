#!/bin/bash
set -e

# Make deploy script executable (distractor)
chmod +x /workspace/scripts/deploy/restart.sh

echo "Sandbox ready. Workspace: /workspace"
echo "Target config: /workspace/openclaw.json"