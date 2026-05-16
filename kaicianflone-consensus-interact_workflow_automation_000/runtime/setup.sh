#!/usr/bin/env bash
set -euo pipefail

echo "=== Setting up consensus-tools sandbox ==="

# Verify consensus-tools is installed
if ! command -v consensus-tools &> /dev/null; then
    echo "ERROR: consensus-tools not found. Installing..."
    npm install -g @consensus-tools/consensus-tools
fi

echo "consensus-tools version: $(consensus-tools --version 2>/dev/null || echo 'unknown')"

# Make deprecated scripts non-executable (they should not be used)
chmod -x /workspace/scripts/deprecated/old_vote_tallier.sh 2>/dev/null || true

# Ensure workspace permissions
chown -R root:root /workspace 2>/dev/null || true
chmod -R 755 /workspace

echo "=== Setup complete ==="
echo "Workspace contents:"
ls -la /workspace/