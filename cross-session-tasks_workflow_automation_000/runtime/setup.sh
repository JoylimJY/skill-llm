#!/bin/bash
set -e

# Ensure workspace permissions
chmod -R 755 /workspace

# Confirm the structure was created
echo "=== Workspace structure ==="
find /workspace -type f | sort

echo ""
echo "=== Setup complete ==="