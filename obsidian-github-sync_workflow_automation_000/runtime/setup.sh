#!/bin/bash
set -e

# Make scripts executable
chmod +x /workspace/scripts/obsidian-sync.sh
chmod +x /workspace/scripts/check-conflict.sh
chmod +x /workspace/backup.sh 2>/dev/null || true

# Ensure git global config is set for the agent
git config --global user.email "agent@test.local"
git config --global user.name "Agent"
git config --global init.defaultBranch master
git config --global pull.rebase true

echo "Setup complete."
echo "Vault dir: /workspace/my-notes-vault"
echo "Bare remote: /workspace/remote-bare-repo.git"
echo "Scripts: /workspace/scripts/"