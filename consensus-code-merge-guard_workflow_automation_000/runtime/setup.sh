#!/usr/bin/env bash
set -e

cd /workspace

echo "=== Setting up consensus-code-merge-guard environment ==="

# Install the npm package locally so run.js is available
npm install consensus-code-merge-guard --registry https://registry.npmjs.org 2>&1 | tail -5

# Verify tsx is available
which tsx || npm install -g tsx --registry https://registry.npmjs.org

# Create the board state directories that the env vars will point to
mkdir -p /workspace/board-state/decisions
mkdir -p /workspace/board-state/personas

# Set permissions
chmod -R 755 /workspace/board-state

echo "=== Setup complete ==="
echo "node_modules present: $(ls node_modules | head -5)"
echo "run.js location: $(find /workspace/node_modules -name 'run.js' 2>/dev/null | head -3)"