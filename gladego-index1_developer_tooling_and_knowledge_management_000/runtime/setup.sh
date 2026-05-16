#!/bin/bash
set -e

echo "=== PayBridge workspace setup ==="

# Ensure workspace permissions
chmod -R 755 /workspace

# Verify index1 is installed and working
echo "Checking index1 installation..."
index1 --version || { echo "ERROR: index1 not found"; exit 1; }

# Run index1 doctor to verify environment
echo "Running index1 doctor..."
index1 doctor || true

echo "=== Setup complete ==="
echo "Workspace contents:"
find /workspace -type f | sort