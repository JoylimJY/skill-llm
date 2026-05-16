#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod +x /workspace/scripts/deploy.sh 2>/dev/null || true

echo "Setup complete. Workspace ready for agent."
ls /workspace/