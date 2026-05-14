#!/bin/bash
set -e

# Export the workspace env variable so scripts can find files
export OPENCLAW_WORKSPACE=/workspace

# Ensure the workspace marker is readable
chmod 644 /workspace/.openclaw_workspace_marker 2>/dev/null || true

# Ensure memory dir exists
mkdir -p /workspace/memory

echo "Setup complete. OPENCLAW_WORKSPACE=/workspace"
echo "Workspace contents:"
ls -la /workspace/