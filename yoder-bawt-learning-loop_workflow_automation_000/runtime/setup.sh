#!/bin/bash
set -e

WORKSPACE="/workspace"

# Ensure all scripts are executable
chmod +x "$WORKSPACE/init.sh" 2>/dev/null || true
chmod +x "$WORKSPACE/confidence-decay.sh" 2>/dev/null || true
chmod +x "$WORKSPACE/promote-rules.sh" 2>/dev/null || true
chmod +x "$WORKSPACE/export-rules.sh" 2>/dev/null || true

# Verify python3 and flock are available
python3 --version
flock --version 2>/dev/null || echo "flock available via util-linux"

echo "Setup complete. Workspace ready at $WORKSPACE"
ls -la "$WORKSPACE/"*.sh