#!/usr/bin/env bash
set -e

# Ensure the workspace index.js is executable
chmod +x /workspace/index.js 2>/dev/null || true

# Confirm node is available
node --version
echo "Setup complete."