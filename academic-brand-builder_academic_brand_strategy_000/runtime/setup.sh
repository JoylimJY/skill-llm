#!/bin/bash
set -e

echo "Setting up workspace..."

chmod -R 755 /workspace

echo "Workspace ready."
tree /workspace 2>/dev/null || find /workspace -type f | sort