#!/bin/bash
set -e

echo "Setting up workspace..."
chmod -R 755 /workspace

echo "Workspace ready. Contents:"
find /workspace -type f | sort

echo ""
echo "Setup complete."