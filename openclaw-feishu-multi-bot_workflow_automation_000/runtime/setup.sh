#!/usr/bin/env bash
set -e

# Make setup script executable
chmod +x /workspace/scripts/setup-feishu-bots.sh

# Ensure jq is available (already installed in Dockerfile)
echo "Setup complete. Workspace ready."
ls -la /workspace/