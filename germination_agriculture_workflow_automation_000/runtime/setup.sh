#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_DIR="${WORKSPACE_DIR:-/workspace}"

# Make the skill script executable
chmod +x "$WORKSPACE_DIR/scripts/script.sh"

# Ensure GERMINATION_DIR default exists (mirrors what the script would create)
mkdir -p "$HOME/.germination"

echo "Setup complete. scripts/script.sh is executable."