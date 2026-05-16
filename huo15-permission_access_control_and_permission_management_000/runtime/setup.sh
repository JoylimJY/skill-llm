#!/usr/bin/env bash
set -e

# Ensure the workspace is owned correctly
chmod -R 755 /workspace

# Create the home directory structure that the skill expects
# (the agent must discover and use the exact path ~/.openclaw/workspace/skills/huo15-permission/)
mkdir -p /root/.openclaw/workspace/skills/

echo "Setup complete. Task workspace ready at /workspace"
echo "Home directory structure initialized."