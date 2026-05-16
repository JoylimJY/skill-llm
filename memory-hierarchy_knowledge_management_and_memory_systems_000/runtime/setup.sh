#!/bin/bash
set -e

# Make scripts executable
chmod +x /workspace/scripts/cleanup.sh

# Ensure memory directory exists (subdirs are agent's responsibility)
mkdir -p /workspace/memory

echo "Setup complete. Workspace ready."
echo ""
echo "Directory structure:"
tree /workspace --dirsfirst -L 3