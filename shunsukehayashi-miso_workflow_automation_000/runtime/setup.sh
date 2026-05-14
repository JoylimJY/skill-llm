#!/bin/bash
set -e

echo "Setting up workspace..."

chmod -R 755 /workspace

# Ensure the ops/missions output directory exists
mkdir -p /workspace/workspace/ops/missions

echo "Setup complete. Workspace ready."
echo ""
echo "Directory structure:"
tree /workspace/workspace/ 2>/dev/null || find /workspace/workspace -type f | sort