#!/bin/bash
set -e

echo "=== Setting up tokenmeter environment ==="

# Install tokenmeter from the public GitHub repo
mkdir -p ~/clawd
cd ~/clawd

if [ ! -d "tokenmeter" ]; then
    git clone https://github.com/jugaad-lab/tokenmeter.git
fi

cd ~/clawd/tokenmeter

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -e .
fi

echo "=== tokenmeter installed ==="

# Verify installation
source ~/clawd/tokenmeter/.venv/bin/activate
tokenmeter --help || echo "tokenmeter help check done"

# Set up the expected session directories for OpenClaw auto-discovery
# (so that 'tokenmeter scan' works if the agent tries it)
mkdir -p ~/.clawdbot/agents/legalbot/sessions/
mkdir -p ~/.clawdbot/agents/researchbot/sessions/

echo "=== Setup complete ==="
echo "Session logs are in /workspace/company/tech/logs/"
echo "Task brief is in /workspace/TASK_BRIEF.txt"