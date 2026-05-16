#!/bin/bash
set -e

echo "=== Setting up workspace ==="

# Make the mock create_team.mjs executable
chmod +x /workspace/scripts/create_team.mjs

# Verify node is available
node --version
echo "Node.js available."

# Verify the workspace structure
echo "=== Workspace structure ==="
find /workspace -type f | sort

echo "=== Setup complete ==="