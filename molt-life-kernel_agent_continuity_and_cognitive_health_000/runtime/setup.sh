#!/bin/bash
set -e

echo "=== Setting up molt-life-kernel environment ==="

# Ensure the workspace node_modules directory exists and has molt-life-kernel
cd /workspace
npm init -y > /dev/null 2>&1 || true

# Install molt-life-kernel locally in the workspace
npm install molt-life-kernel 2>&1 | tail -5

echo "=== molt-life-kernel installed ==="

# Verify the module is loadable
node -e "const m = require('molt-life-kernel'); console.log('Module keys:', Object.keys(m));" 2>&1 || \
node -e "import('molt-life-kernel').then(m => console.log('ESM Module keys:', Object.keys(m))).catch(e => console.log('Import error:', e.message));" 2>&1 || true

echo "=== Setup complete ==="