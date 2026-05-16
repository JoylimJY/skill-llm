#!/bin/bash
set -e

# Ensure scripts directory scripts are executable
chmod +x /workspace/scripts/init-novel.sh 2>/dev/null || true

# Verify workspace structure
echo "=== Workspace structure ==="
find /workspace -type f | head -30
echo "=== Setup complete ==="