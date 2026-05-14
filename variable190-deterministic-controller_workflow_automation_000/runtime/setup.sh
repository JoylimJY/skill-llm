#!/usr/bin/env bash
set -e

# Make sure the workspace directories are accessible
chmod -R 755 /workspace/skills
chmod -R 755 /workspace/robotics-fleet-workspace

echo "Setup complete. Workspace layout:"
find /workspace -maxdepth 4 -type f | sort