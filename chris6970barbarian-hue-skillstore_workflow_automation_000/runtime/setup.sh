#!/bin/bash
set -e

WORKSPACE="/workspace"
SKILLSTORE_DIR="$WORKSPACE/skillstore"

# Make main.js executable
chmod +x "$SKILLSTORE_DIR/main.js"

# Install skillstore as a global CLI command
ln -sf "$SKILLSTORE_DIR/main.js" /usr/local/bin/skillstore
chmod +x /usr/local/bin/skillstore

# Verify node is available
node --version

# Create OpenClaw skills directory
mkdir -p ~/.openclaw/workspace/skills

# Quick sanity check
echo "=== skillstore known (sanity check) ==="
skillstore known | head -5
echo "=== Setup complete ==="