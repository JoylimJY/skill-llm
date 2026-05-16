#!/bin/bash
set -e

echo "=== Setting up workspace permissions ==="
chmod -R 755 /workspace

echo "=== Workspace structure ==="
find /workspace -type f | sort

echo "=== Setup complete ==="