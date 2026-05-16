#!/bin/bash
set -e

# Ensure memory directory exists and is writable
mkdir -p /workspace/memory
chmod 755 /workspace/memory

# Ensure all workspace files are readable
find /workspace -type f -exec chmod 644 {} \;
find /workspace -type d -exec chmod 755 {} \;

echo "Setup complete. Workspace ready."
ls -la /workspace/