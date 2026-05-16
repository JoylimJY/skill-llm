#!/bin/bash
set -e

# Install mock openclaw binary to PATH
cp /workspace/.openclaw_state/openclaw_bin.sh /usr/local/bin/openclaw
chmod +x /usr/local/bin/openclaw

# Make all skill scripts executable
chmod +x /workspace/skills/openclaw-github-copilot/scripts/copilot-status.sh
chmod +x /workspace/skills/openclaw-github-copilot/scripts/copilot-activate.sh
chmod +x /workspace/skills/openclaw-github-copilot/scripts/copilot-quickstart.sh

# Make distractor scripts executable too (realistic)
chmod +x /workspace/scripts/deploy.sh
chmod +x /workspace/scripts/lint.sh

# Verify openclaw is on PATH
openclaw models list --plain > /dev/null 2>&1 && echo "openclaw mock ready" || echo "WARNING: openclaw mock failed"

echo "Setup complete. Initial state:"
cat /workspace/.openclaw_state/state.json