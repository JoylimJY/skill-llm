#!/bin/bash
set -e

# Ensure openclaw workspace structure is properly initialized
mkdir -p /root/.openclaw/workspace/memory
mkdir -p /root/.openclaw/workspace/skills
mkdir -p /root/.openclaw/workspace/logs

# Ensure kpi.md does NOT exist before agent runs
rm -f /root/.openclaw/workspace/memory/kpi.md

# Confirm setup
echo "✅ Setup complete. KPI file cleared."
echo "📂 Workspace structure:"
tree /root/.openclaw/workspace/ 2>/dev/null || ls -la /root/.openclaw/workspace/
echo ""
echo "📂 Task workspace:"
tree /workspace/ 2>/dev/null || ls -la /workspace/