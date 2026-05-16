#!/bin/bash
set -e

echo "=== Setting up workspace ==="

cd /workspace

# Make scripts executable
chmod +x scripts/backtest_runner.sh 2>/dev/null || true

# Verify Node.js is available
node --version
npm --version

echo "=== Workspace setup complete ==="
echo "Directory structure:"
find . -type f | head -40