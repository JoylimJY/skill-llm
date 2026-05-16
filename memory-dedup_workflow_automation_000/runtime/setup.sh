#!/bin/bash
set -e

# Make the dedup script executable
chmod +x /workspace/skills/memory-dedup/dedup.mjs

# Verify Node.js is available
node --version

# Verify the workspace structure
echo "=== Workspace structure ==="
ls /workspace/
echo ""
echo "=== MEMORY.md preview ==="
head -20 /workspace/MEMORY.md
echo ""
echo "Setup complete."