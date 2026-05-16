#!/bin/bash
set -e

# Ensure workspace permissions
chmod -R 755 /workspace

echo "=== Workspace structure ==="
find /workspace -type f | sort

echo "=== Setup complete ==="