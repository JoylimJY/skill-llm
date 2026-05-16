#!/usr/bin/env bash
set -e

echo "=== Setup: no mock servers needed for this task ==="

# Make workspace contents readable
find /workspace -type f -exec chmod 644 {} \;
find /workspace -type d -exec chmod 755 {} \;

echo "=== Workspace ready ==="
tree /workspace 2>/dev/null || find /workspace -type f | sort