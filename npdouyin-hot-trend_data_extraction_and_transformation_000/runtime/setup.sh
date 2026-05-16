#!/bin/bash
set -e

# Make the douyin.js script executable
chmod +x /workspace/scripts/douyin.js

# Verify node is available
node --version

# Quick smoke test of the mock script
echo "Smoke test: node scripts/douyin.js hot 3"
cd /workspace && node scripts/douyin.js hot 3

echo "Setup complete."