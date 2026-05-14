#!/bin/bash
set -e

cd /workspace

# Download the ai_agent_tools library from GitHub
wget -q https://raw.githubusercontent.com/cerbug45/ai-agent-tools/main/ai_agent_tools.py -O /workspace/ai_agent_tools.py

echo "ai_agent_tools.py downloaded."
python /workspace/ai_agent_tools.py 2>/dev/null | tail -1 || true
echo "Setup complete. Workspace ready."
ls /workspace/