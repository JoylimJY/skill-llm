#!/bin/bash
set -e

# Ensure the workspace and home directories have correct permissions
chmod -R 755 /workspace
chmod 700 ~/.openclaw

# Make cron scripts executable (distractor files)
chmod +x /workspace/crons/scripts/fetch_prices.sh
chmod +x /workspace/crons/scripts/rebalance.sh

echo "Setup complete. Workspace ready."
echo "OpenClaw config location: $HOME/.openclaw/openclaw.json"
echo "Template files available in: /workspace/templates/"