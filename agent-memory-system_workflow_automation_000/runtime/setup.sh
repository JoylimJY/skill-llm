#!/bin/bash
set -euo pipefail

echo "=== Setting up agent-memory-system sandbox ==="

# Ensure all scripts are executable
chmod +x /workspace/scripts/*.sh
chmod +x /workspace/.openclaw/workspace/skills/agent-memory-system/scripts/*.sh

# Set WORKSPACE env variable
export WORKSPACE=/workspace
echo "export WORKSPACE=/workspace" >> /etc/environment
echo "export WORKSPACE=/workspace" >> /root/.bashrc

# Ensure logs directory exists
mkdir -p /workspace/logs

# Fix the extract-skill.sh which has a shell syntax error (head-1 should be head -1)
# This is an intentional quirk the agent must work around or the script handles gracefully
sed -i 's/head-1/head -1/' /workspace/scripts/extract-skill.sh
sed -i 's/head-1/head -1/' /workspace/.openclaw/workspace/skills/agent-memory-system/scripts/extract-skill.sh

echo "=== Setup complete ==="
echo "Workspace: /workspace"
echo "Scripts available at: /workspace/scripts/"
ls -la /workspace/scripts/
echo ""
echo "Memory files:"
ls -la /workspace/memory/*.md 2>/dev/null | head -20