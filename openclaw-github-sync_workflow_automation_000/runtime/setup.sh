#!/usr/bin/env bash
set -euo pipefail

# Make all skill scripts executable
chmod +x /workspace/.openclaw/workspace/scripts/sync.sh
chmod +x /workspace/.openclaw/workspace/scripts/pull.sh
chmod +x /workspace/.openclaw/workspace/scripts/create_private_repo.sh

# Configure git globals (safe for the workspace)
git config --global user.email "agent@test.local"
git config --global user.name "Agent Test"
git config --global init.defaultBranch main

# Mark all workspace git dirs as safe
git config --global --add safe.directory '*'

echo "Setup complete."
echo "Skill workspace: /workspace/.openclaw/workspace"
echo "Mock remote:     /workspace/fake-remote.git"