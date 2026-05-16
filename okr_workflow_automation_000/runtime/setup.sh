#!/usr/bin/env bash
set -e

WORKSPACE_DIR="${WORKSPACE_DIR:-/workspace}"

# Ensure the .openclaw memory directory exists (agent must still create the file)
mkdir -p "${WORKSPACE_DIR}/.openclaw/workspace/memory"

# Export workspace-relative HOME so ~/ resolves correctly inside container
# The agent should write to ~/.openclaw/workspace/memory/okr.md
# In this container, HOME=/root, so we symlink to make the path consistent
if [ ! -d "/root/.openclaw" ]; then
    mkdir -p /root/.openclaw
fi

# Create a symlink so ~/.openclaw resolves to the workspace's .openclaw
# Only create if it doesn't exist
if [ ! -L "/root/.openclaw/workspace" ] && [ ! -d "/root/.openclaw/workspace" ]; then
    ln -s "${WORKSPACE_DIR}/.openclaw/workspace" /root/.openclaw/workspace
fi

echo "Setup complete. Agent should write to: ~/.openclaw/workspace/memory/okr.md"
echo "Which resolves to: /root/.openclaw/workspace/memory/okr.md"
echo "Which is linked to: ${WORKSPACE_DIR}/.openclaw/workspace/memory/okr.md"