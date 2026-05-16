#!/usr/bin/env bash
set -e

# Ensure the wizard script is executable
chmod +x /workspace/openclaw_project/scripts/memory-onboarding-wizard.py

# Create the target custom workspace directory that the agent must use
mkdir -p /workspace/openclaw_project/agent_workspace

echo "Setup complete."
echo "OpenClaw project root: /workspace/openclaw_project"
echo "Target agent workspace: /workspace/openclaw_project/agent_workspace"