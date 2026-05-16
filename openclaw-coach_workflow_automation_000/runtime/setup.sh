#!/bin/bash
set -e

chmod +x /workspace/scripts/sync-docs.sh
chmod +x /workspace/scripts/pick-daily-tip.sh
chmod +x /workspace/scripts/send-daily-tip.sh

echo "Setup complete. Workspace ready."
ls -la /workspace/
echo "Obsidian structure:"
find /workspace/Obsidian -type f | sort