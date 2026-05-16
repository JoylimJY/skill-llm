#!/bin/bash
set -e

echo "=== Setting up workspace ==="

chmod +x /workspace/scripts/deploy.sh 2>/dev/null || true

echo "=== Workspace ready ==="
tree /workspace --dirsfirst -L 4 2>/dev/null || find /workspace -type f | sort