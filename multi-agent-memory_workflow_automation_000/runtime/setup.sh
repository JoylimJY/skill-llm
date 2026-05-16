#!/bin/bash
set -e

echo "=== Setting up multi-agent-memory task environment ==="

# Ensure skill scripts are executable
chmod +x /root/.openclaw/skills/multi-agent-memory/scripts/init-project.sh 2>/dev/null || true
chmod +x /root/.openclaw/skills/multi-agent-memory/scripts/daily-check.sh 2>/dev/null || true

# Verify the workspace was generated
if [ ! -d "/root/.openclaw/projects/phoenix-engine" ]; then
    echo "ERROR: Workspace not generated properly"
    exit 1
fi

echo "=== Environment ready ==="
echo "Project: phoenix-engine"
echo "Agent: maker"
echo "Current status files:"
ls -la /root/.openclaw/projects/phoenix-engine/status/
echo ""
echo "Knowledge base:"
ls -la /root/.openclaw/knowledge/decisions/