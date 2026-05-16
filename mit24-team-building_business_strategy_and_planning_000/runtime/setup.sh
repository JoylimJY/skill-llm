#!/bin/bash
set -e

echo "Setting up workspace..."
cd /workspace

# Ensure all workspace files have proper permissions
find /workspace -type f -exec chmod 644 {} \;
find /workspace -type d -exec chmod 755 {} \;

echo "Workspace ready."
tree /workspace 2>/dev/null || find /workspace -type f | sort