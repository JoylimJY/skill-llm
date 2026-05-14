#!/bin/bash
set -e

echo "=== AlephNet Node Setup ==="

# Ensure alephnet-node CLI is accessible
which alephnet-node || {
    echo "Attempting to locate alephnet-node..."
    find /usr /opt /root -name "alephnet-node" -type f 2>/dev/null | head -5
    # Try npm global bin
    NPM_BIN=$(npm bin -g 2>/dev/null || echo "")
    if [ -n "$NPM_BIN" ] && [ -f "$NPM_BIN/alephnet-node" ]; then
        ln -sf "$NPM_BIN/alephnet-node" /usr/local/bin/alephnet-node
    fi
}

# Verify installation
alephnet-node status 2>/dev/null || echo "AlephNet node status check complete (may run in offline mode)"

# Set workspace permissions
chmod -R 755 /workspace

echo "=== Setup Complete ==="
echo "Workspace: /workspace"
echo "Task brief: /workspace/task_brief.json"