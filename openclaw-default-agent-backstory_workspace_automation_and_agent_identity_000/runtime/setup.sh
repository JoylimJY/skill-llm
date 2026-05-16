#!/bin/bash
set -e

echo "=== Setting up workspace permissions ==="
chmod -R 755 /workspace

echo "=== Workspace structure ==="
tree /workspace --dirsfirst -L 3 2>/dev/null || find /workspace -maxdepth 3 | sort

echo "=== Setup complete ==="