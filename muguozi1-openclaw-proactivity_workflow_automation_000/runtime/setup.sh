#!/bin/bash
set -e

# Make all shell scripts executable
find /workspace/infra/scripts -name "*.sh" -exec chmod +x {} \;

# Ensure the home directory proactivity folder has correct permissions
mkdir -p ~/proactivity/memory
chmod -R 755 ~/proactivity

echo "Setup complete."
echo "Workspace structure:"
find /workspace -type f | head -30
echo ""
echo "Current proactivity state:"
find ~/proactivity -type f 2>/dev/null || echo "(empty or missing)"