#!/usr/bin/env bash
set -euo pipefail

echo "=== Council Builder Sandbox Setup ==="

# Make the init script executable
chmod +x /workspace/scripts/init-council.sh

# Verify the script is runnable
echo "Verifying init-council.sh is executable..."
ls -la /workspace/scripts/init-council.sh

echo "=== Workspace structure ==="
find /workspace -type f | sort | head -60

echo "=== Setup complete ==="