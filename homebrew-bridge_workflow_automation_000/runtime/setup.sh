#!/usr/bin/env bash
set -euo pipefail

# Ensure scripts are executable
chmod +x /workspace/scripts/*.sh

# Ensure /home/node/.openclaw exists and has right permissions
mkdir -p /home/node/.openclaw
chmod 755 /home/node/.openclaw

echo "Setup complete. Scripts ready in /workspace/scripts/"
echo "OpenClaw config at /home/node/.openclaw/openclaw.json"