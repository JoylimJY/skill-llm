#!/bin/bash
set -e

echo "=== Family Steward Setup ==="

cd /workspace/family-steward

# Ensure dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install --registry https://registry.npmmirror.com
fi

# Ensure the data directory exists
mkdir -p data

# Make CLI executable if it exists
if [ -f "bin/steward.js" ]; then
    chmod +x bin/steward.js
fi

if [ -f "index.js" ]; then
    chmod +x index.js
fi

# Check if TypeScript needs compilation
if [ -f "tsconfig.json" ] && [ -d "src" ]; then
    echo "Building TypeScript..."
    npm run build 2>/dev/null || npx tsc 2>/dev/null || echo "Build step skipped (may not be needed)"
fi

echo "=== Setup Complete ==="
ls -la /workspace/family-steward/
echo "Data directory: $(ls /workspace/family-steward/data/ 2>/dev/null || echo 'empty')"