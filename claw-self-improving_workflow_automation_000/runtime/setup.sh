#!/bin/bash
set -e

# Ensure the self-improving directory is accessible
chmod -R 755 ~/self-improving/

# Print initial state for debugging
echo "=== Initial memory.md line count ==="
wc -l ~/self-improving/memory.md

echo "=== Initial corrections.md line count ==="
wc -l ~/self-improving/corrections.md

echo "=== Directory structure ==="
find ~/self-improving/ -type f | sort

echo "Setup complete."