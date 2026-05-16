#!/bin/bash
set -e

# Ensure the home directory structure is clean
mkdir -p /root/.openclaw
chmod 755 /root/.openclaw

# Ensure /root is the home directory
export HOME=/root

# Verify .openclaw exists but workspace subdir does NOT (agent must create it)
if [ -d "/root/.openclaw/workspace" ]; then
    echo "WARNING: workspace dir already exists, removing for clean test"
    rm -rf /root/.openclaw/workspace
fi

echo "Setup complete. /root/.openclaw exists, /root/.openclaw/workspace does NOT exist."
echo "Agent must create ~/.openclaw/workspace/SOUL.md with correct content."