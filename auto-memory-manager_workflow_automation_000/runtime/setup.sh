#!/usr/bin/env bash
set -e

# Ensure memory-manager is importable from its own directory
chmod -R 755 /workspace/memory-manager/

# Create a small wrapper so the agent can run scripts from the workspace root
# without needing to know the internal path trickery
echo "Setup complete. Workspace ready."
ls /workspace/