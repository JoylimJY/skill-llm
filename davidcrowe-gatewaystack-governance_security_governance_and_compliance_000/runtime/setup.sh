#!/bin/bash
set -e

echo "[setup] Verifying plugin skeleton..."
PLUGIN_DIR="$HOME/.openclaw/plugins/gatewaystack-governance"

if [ ! -f "$PLUGIN_DIR/policy.example.json" ]; then
    echo "[setup] ERROR: policy.example.json not found at $PLUGIN_DIR"
    exit 1
fi

echo "[setup] policy.example.json is present."

# Ensure policy.json does NOT exist at task start
if [ -f "$PLUGIN_DIR/policy.json" ]; then
    echo "[setup] WARNING: policy.json already exists — removing for clean start."
    rm "$PLUGIN_DIR/policy.json"
fi

# Make workspace scripts executable (distractors)
chmod +x /home/agentuser/workspace/scripts/deploy.sh
chmod +x /home/agentuser/workspace/scripts/health_check.sh

# Ensure npm global dir exists
mkdir -p "$HOME/.npm-global/lib"

echo "[setup] Setup complete. Task environment is ready."