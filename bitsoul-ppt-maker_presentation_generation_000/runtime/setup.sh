#!/bin/bash
set -e

echo "=== Setting up workspace ==="

# Ensure workspace permissions are correct
chmod -R 755 /workspace

echo "=== Workspace ready ==="
ls -la /workspace/
echo "=== Setup complete ==="