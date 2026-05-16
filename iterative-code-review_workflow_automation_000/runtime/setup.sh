#!/bin/bash
set -e

# Ensure git is configured
git config --global user.email "agent@test.local"
git config --global user.name "Test Agent"

# Make openclaw mock executable
chmod +x /usr/local/bin/openclaw

# Ensure the payment-service repo has proper git remote-like refs
cd /workspace/payment-service

# Verify the branch structure
echo "=== Git branch status ==="
git log --oneline -5
echo "=== Remotes ==="
git branch -a

# Create a home directory structure hint (the .openclaw parent dir should NOT pre-exist)
# The agent must create the full path
mkdir -p /root/.openclaw/workspace  2>/dev/null || true
# DO NOT create the .iterative-code-review subdirectory - agent must do this

echo "=== Setup complete ==="
echo "Workspace contents:"
ls /workspace/