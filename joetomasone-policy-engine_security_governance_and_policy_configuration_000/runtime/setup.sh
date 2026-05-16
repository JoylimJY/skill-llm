#!/bin/bash
set -e

echo "Setting up sandbox environment..."

# Ensure workspace permissions
chmod -R 755 /workspace

# Make scripts executable
find /workspace/scripts -name "*.sh" -exec chmod +x {} \;

echo "Sandbox setup complete."
echo "Workspace contents:"
tree /workspace --noreport -L 3 2>/dev/null || find /workspace -maxdepth 3 -print