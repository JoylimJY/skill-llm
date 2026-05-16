#!/usr/bin/env bash
set -e

# Ensure workspace permissions
chmod -R 755 /workspace

# Create a simple helper symlink so the agent can find skill docs easily
ln -sf /workspace/skill_docs /workspace/contracts/skill_docs 2>/dev/null || true

echo "Setup complete. Workspace ready."