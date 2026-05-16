#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${WORKSPACE:-/workspace}"

# Ensure script is executable
chmod +x "$WORKSPACE/scripts/script.sh"

# Ensure data store directory exists
mkdir -p "$HOME/.local/share/bundle"

echo "Setup complete. Workspace: $WORKSPACE"
echo "Script ready at: $WORKSPACE/scripts/script.sh"