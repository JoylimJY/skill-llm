#!/bin/bash
set -e

echo "=== Setting up workspace permissions ==="
chmod +x /workspace/project/tools/wc_helper.sh 2>/dev/null || true

# Create the output directories the agent should use
mkdir -p /workspace/project/chapters

echo "=== Setup complete ==="
echo "Workspace contents:"
find /workspace -type f | sort