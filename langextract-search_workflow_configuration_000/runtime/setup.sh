#!/usr/bin/env bash
set -e

# Make scripts executable
chmod +x /workspace/scripts/search.py 2>/dev/null || true

# Confirm workspace structure
echo "=== Workspace structure ==="
find /workspace -type f | sort

echo "=== Setup complete ==="