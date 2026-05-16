#!/bin/bash
set -e

echo "=== Setup: Configuring workspace permissions ==="
chmod -R 755 /workspace
find /workspace -name "*.md" -exec chmod 644 {} \;
find /workspace -name "*.txt" -exec chmod 644 {} \;
find /workspace -name "*.yaml" -exec chmod 644 {} \;

echo "=== Setup complete. Workspace ready. ==="
echo "Directory structure:"
tree /workspace 2>/dev/null || find /workspace -type f | sort