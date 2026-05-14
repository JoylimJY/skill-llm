#!/usr/bin/env bash
set -euo pipefail

echo "=== Setting up sandbox runtime ==="

# Fix permissions on scripts
chmod +x /workspace/projects/my-openclaw/scripts/update.sh
chmod +x /workspace/projects/my-openclaw/scripts/deploy.sh
chmod +x /workspace/projects/my-openclaw/scripts/rollback.sh
chmod +x /workspace/projects/my-openclaw/scripts/health-check.sh

# Ensure all workspace files owned by agent
chown -R agent:agent /workspace
chown -R agent:agent /home/agent

# Set up git config for agent user (belt-and-suspenders)
su - agent -c "git config --global user.email 'agent@test.local'"
su - agent -c "git config --global user.name 'Agent Test'"
su - agent -c "git config --global init.defaultBranch main"

# Verify the upstream bare repo has the dev/integration branch
echo "=== Verifying upstream bare repo ==="
git --git-dir=/workspace/_upstream_bare.git branch -a

# Verify local project state
echo "=== Verifying local project state ==="
su - agent -c "cd /workspace/projects/my-openclaw && git log --oneline -3"
su - agent -c "cd /workspace/projects/my-openclaw && git remote -v"

echo "=== Sandbox ready ==="
echo "Agent should update OpenClaw at: /workspace/projects/my-openclaw"
echo "Branch: dev/integration"
echo "Script: /workspace/projects/my-openclaw/scripts/update.sh"