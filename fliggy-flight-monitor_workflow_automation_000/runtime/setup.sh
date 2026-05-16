#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace
chmod +x /workspace/scripts/fetch_prices.sh 2>/dev/null || true

# Create the memory directory structure base (but NOT the specific monitoring file - agent must create it)
mkdir -p /workspace/memory/flight-monitor

echo "Setup complete. Workspace ready."
echo "Task brief:"
cat /workspace/task_brief.txt