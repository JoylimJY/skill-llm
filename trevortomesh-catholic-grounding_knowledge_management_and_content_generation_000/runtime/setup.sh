#!/bin/bash
set -e

WORKSPACE="/workspace"

# Ensure scripts are executable
chmod +x "$WORKSPACE/scripts/ccc.sh"
chmod +x "$WORKSPACE/scripts/prayer.sh"
chmod +x "$WORKSPACE/scripts/status.sh"

# Verify scripts work
echo "=== Verifying script: ccc.sh ==="
cd "$WORKSPACE" && ./scripts/ccc.sh "purgatory"

echo ""
echo "=== Verifying script: prayer.sh ==="
cd "$WORKSPACE" && ./scripts/prayer.sh "eternal rest"

echo ""
echo "=== Verifying script: status.sh ==="
cd "$WORKSPACE" && ./scripts/status.sh

echo ""
echo "Setup complete. Workspace ready for agent."