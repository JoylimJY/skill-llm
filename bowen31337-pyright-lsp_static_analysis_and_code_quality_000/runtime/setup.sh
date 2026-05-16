#!/bin/bash
set -e

echo "=== Setting up trade_analytics workspace ==="

cd /workspace/trade_analytics

# Ensure scripts are executable
chmod +x scripts/deploy.sh 2>/dev/null || true

# Verify pyright is available
which pyright && pyright --version || echo "WARNING: pyright not found in PATH"

echo "=== Setup complete ==="
echo "Project root: /workspace/trade_analytics"
echo "Run 'cd /workspace/trade_analytics && pyright' to check types"