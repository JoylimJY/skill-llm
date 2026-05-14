#!/bin/bash
set -e

# Ensure the seasonal_planting.py tool is executable
chmod +x /workspace/seasonal_planting.py

# Ensure openclaw workspace directory exists
mkdir -p /root/.openclaw/workspace

# Make the tool accessible system-wide
ln -sf /workspace/seasonal_planting.py /usr/local/bin/seasonal_planting.py
chmod +x /usr/local/bin/seasonal_planting.py

echo "Setup complete."
echo "Tool location: /workspace/seasonal_planting.py"
echo "Openclaw workspace: /root/.openclaw/workspace"