#!/bin/bash
set -e

# Make all scripts executable
chmod +x /root/.openclaw/workspace/skills/marcus-investment-analyst/scripts/*.py

echo "Setup complete. Scripts are executable."
echo "Workspace structure:"
find /root/.openclaw/workspace/skills/marcus-investment-analyst -type f | sort
echo ""
echo "Market snapshot at: /workspace/market_snapshot.json"