#!/bin/bash
set -e

# Set default WORKSPACE_DIR if not set
WORKSPACE_DIR="${WORKSPACE_DIR:-/workspace}"

# Make all scripts executable
find "$WORKSPACE_DIR/scripts" -name "*.py" -exec chmod +x {} \;

# Ensure inventory directory exists and is empty/fresh
INV_DIR="$HOME/.openclaw/workspace/homelab-assets"
mkdir -p "$INV_DIR"
echo '{"assets":[]}' > "$INV_DIR/inventory.json"

echo "Setup complete. Inventory reset to empty at $INV_DIR/inventory.json"