#!/bin/bash
set -e

echo "Setting up workspace..."

# Ensure all raw feed files are readable
chmod -R 644 /workspace/raw_feeds/ 2>/dev/null || true
chmod -R 755 /workspace/raw_feeds/ 2>/dev/null || true

echo "Setup complete. Workspace is ready."
ls -la /workspace/