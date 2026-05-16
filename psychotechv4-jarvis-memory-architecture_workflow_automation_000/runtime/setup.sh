#!/bin/bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace

# Verify key files exist
echo "=== Setup verification ==="
echo "Cron inbox:"
cat /workspace/memory/cron-inbox.md
echo ""
echo "Heartbeat state:"
cat /workspace/memory/heartbeat-state.json
echo ""
echo "=== Setup complete ==="