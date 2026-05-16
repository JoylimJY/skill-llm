#!/usr/bin/env bash
set -e

# Ensure the mock openclaw binary is executable
chmod +x /usr/local/bin/openclaw

# Ensure model_manager.py is executable
MM_PATH="$HOME/.qclaw/workspace/skills/model-manager/scripts/model_manager.py"
if [ -f "$MM_PATH" ]; then
    chmod +x "$MM_PATH"
fi

# Verify openclaw is on PATH
which openclaw && echo "[setup] openclaw mock binary found at $(which openclaw)"

# Verify initial state
echo "[setup] Initial session state:"
cat "$HOME/.qclaw/agents/main/agent/models.json"
echo ""
echo "[setup] Initial global config:"
cat "$HOME/.qclaw/openclaw.json"
echo ""
echo "[setup] Setup complete."