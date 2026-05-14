#!/bin/bash
set -e

# Ensure the token-optimizer CLI is accessible from workspace
if [ -d /opt/token-optimizer ]; then
    echo "[setup] token-optimizer found at /opt/token-optimizer"
    # Symlink cli.py into /workspace for convenience (agent may discover it here or at /opt)
    ln -sf /opt/token-optimizer/cli.py /workspace/cli.py 2>/dev/null || true
    # Copy any requirements
    if [ -f /opt/token-optimizer/requirements.txt ]; then
        pip install -r /opt/token-optimizer/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple -q || true
    fi
else
    echo "[setup] WARNING: /opt/token-optimizer not found, attempting fallback clone"
    git clone https://github.com/smartpeopleconnected/openclaw-token-optimizer.git /opt/token-optimizer || true
    ln -sf /opt/token-optimizer/cli.py /workspace/cli.py 2>/dev/null || true
fi

# Ensure ~/.openclaw/ does NOT pre-exist (clean state for the task)
rm -rf ~/.openclaw/

echo "[setup] Environment ready. Agent must use the token-optimizer CLI to configure OpenClaw."
echo "[setup] Tool location: /opt/token-optimizer/cli.py"