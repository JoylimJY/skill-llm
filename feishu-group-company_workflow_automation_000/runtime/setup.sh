#!/bin/bash
set -e

# Make the apply script executable
chmod +x /workspace/scripts/apply_feishu_group_company.py

# Ensure HOME-relative path works by symlinking workspace .openclaw to HOME
if [ ! -d "$HOME/.openclaw" ]; then
    ln -sf /workspace/.openclaw "$HOME/.openclaw"
fi

echo "Setup complete."
echo "  apply script: /workspace/scripts/apply_feishu_group_company.py"
echo "  config: /workspace/.openclaw/openclaw.json"