#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_DIR="${WORKSPACE_DIR:-/workspace}"

# Make the leads skill script executable
chmod +x "$WORKSPACE_DIR/scripts/script.sh"

# Ensure ~/.leads doesn't exist yet (clean state)
rm -rf "$HOME/.leads"

echo "Setup complete. Workspace: $WORKSPACE_DIR"
echo "Script permissions:"
ls -la "$WORKSPACE_DIR/scripts/script.sh"