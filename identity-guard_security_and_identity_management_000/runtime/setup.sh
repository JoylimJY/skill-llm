#!/bin/bash
set -e

# Make all scripts executable
chmod +x /workspace/scripts/guard.sh
chmod +x /workspace/scripts/init.sh
chmod +x /workspace/scripts/whoami.sh

# Verify identities.json does NOT exist (agent must create it)
if [ -f /workspace/identities.json ]; then
    rm /workspace/identities.json
    echo "Removed stale identities.json"
fi

echo "Setup complete. Workspace ready for agent."
echo "Scripts are executable:"
ls -la /workspace/scripts/