#!/usr/bin/env bash
set -e

# Make the package generator script executable
chmod +x /workspace/scripts/create-package.sh

echo "Setup complete. Workspace ready."
echo "Listing workspace:"
find /workspace -type f | sort