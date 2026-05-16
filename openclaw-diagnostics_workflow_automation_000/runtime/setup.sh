#!/bin/bash
set -e

echo "[setup] Making diagnostic scripts executable..."
chmod +x /root/.openclaw/workspace/skills/openclaw-diagnostics/scripts/get-diagnostic-info.sh
chmod +x /root/.openclaw/workspace/skills/openclaw-diagnostics/scripts/check-common-issues.sh

echo "[setup] Verifying knowledge base exists..."
KB_PATH="/root/.openclaw/workspace/skills/openclaw-diagnostics/assets/default-snapshot.json"
if [ -f "$KB_PATH" ]; then
    PAGE_COUNT=$(python3 -c "import json; d=json.load(open('$KB_PATH')); print(len(d['pages']))")
    echo "[setup] Knowledge base loaded: $PAGE_COUNT pages"
else
    echo "[ERROR] Knowledge base missing!"
    exit 1
fi

echo "[setup] Verifying config exists..."
if [ -f "/root/.openclaw/config.yaml" ]; then
    echo "[setup] OpenClaw config found"
else
    echo "[ERROR] OpenClaw config missing!"
    exit 1
fi

echo "[setup] Workspace ready."
ls /workspace/