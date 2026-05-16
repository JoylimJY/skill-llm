#!/bin/bash
set -e

echo "Setting up Mind Layer evaluation environment..."

# Make setup script executable
chmod +x /workspace/mind-layer/scripts/setup.sh

# Ensure agent_workspace directories exist
mkdir -p /workspace/agent_workspace/memory/archive

echo "Setup complete."