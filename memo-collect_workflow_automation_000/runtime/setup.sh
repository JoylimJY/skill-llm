#!/bin/bash
set -e

echo "Setting up memo-collect environment..."

# Ensure dist directory exists and index.js is executable
chmod +x /workspace/memo-collect/dist/index.js 2>/dev/null || true

# Verify node is available
node --version

# Ensure the memos.json does NOT exist at start (clean slate)
rm -f /workspace/memo-collect/memos.json

# Quick smoke test
cd /workspace/memo-collect
node dist/index.js list_memo
echo "Setup complete. memo-collect is operational."