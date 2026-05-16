#!/bin/bash
set -e

# Ensure workspace permissions
chmod -R 755 /workspace

# Verify the workspace was set up correctly
echo "=== Workspace structure ==="
find /workspace -type f | sort

echo ""
echo "=== MEMORY.md line count ==="
wc -l /workspace/MEMORY.md

echo ""
echo "=== Tasks directory ==="
ls -la /workspace/memory/tasks/

echo ""
echo "=== Today's date ==="
date +%Y-%m-%d

echo ""
echo "Setup complete."