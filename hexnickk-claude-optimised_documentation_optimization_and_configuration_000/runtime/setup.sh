#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace
chmod +x /workspace/scripts/migrate.sh 2>/dev/null || true

echo "Setup complete. Workspace structure:"
find /workspace -type f | sort