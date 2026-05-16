#!/bin/bash
set -e

echo "=== Setting up looking-for-someone skill environment ==="

cd /workspace/looking-for-someone

# Ensure node_modules are installed
if [ ! -d "node_modules" ]; then
    npm install 2>/dev/null || true
fi

# Verify the CLI exists and is executable
if [ -f "scripts/cli.js" ]; then
    chmod +x scripts/cli.js
    echo "CLI found at scripts/cli.js"
else
    echo "WARNING: scripts/cli.js not found — skill may not be installed correctly"
fi

# Ensure data directory exists
DATA_DIR="$HOME/.openclaw/skills-data/looking-for-someone"
mkdir -p "$DATA_DIR"
echo "Data directory ready: $DATA_DIR"

# Quick sanity check
echo "=== Node version ==="
node --version

echo "=== Directory structure ==="
ls -la /workspace/looking-for-someone/

echo "=== Setup complete ==="