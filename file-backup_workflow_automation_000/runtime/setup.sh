#!/bin/bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace

# Make deploy script executable
chmod +x /workspace/deploy/scripts/deploy.sh

echo "Setup complete. Workspace ready."
echo "config.json contents:"
cat /workspace/config.json