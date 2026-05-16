#!/bin/bash
set -e

chmod +x /workspace/scripts/add_asset.py
chmod +x /workspace/scripts/update_asset.py
chmod +x /workspace/scripts/inventory.py
chmod +x /workspace/scripts/report.py
chmod +x /workspace/scripts/search.py

# Ensure the inventory directory exists
mkdir -p ~/.openclaw/workspace/homelab-assets

echo "Setup complete. Scripts are executable."
echo "Workspace contents:"
find /workspace -type f | sort