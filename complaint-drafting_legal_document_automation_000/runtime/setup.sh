#!/bin/bash
set -e

# Ensure correct permissions on workspace
chmod -R 755 /workspace

# Confirm key files exist
echo "=== Workspace structure ==="
find /workspace -type f | sort

echo ""
echo "=== Setup complete. Task workspace is ready. ==="