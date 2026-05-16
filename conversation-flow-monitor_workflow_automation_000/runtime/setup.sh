#!/bin/bash
set -e

# Ensure workspace directory and .learnings exist with correct permissions
chmod -R 755 /workspace
chmod 777 /workspace/.learnings

# Make the manual trigger script executable (distractor)
chmod +x /workspace/ops/adhoc/manual_trigger.sh 2>/dev/null || true

echo "Setup complete. Workspace ready for agent."