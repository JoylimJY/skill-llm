#!/bin/bash
set -e

echo "[setup] Verifying skill script exists..."
SKILL_PATH="/root/.npm-global/lib/node_modules/openclaw/skills/doc-format-gw/format_gw.py"

if [ ! -f "$SKILL_PATH" ]; then
    echo "[setup] ERROR: format_gw.py not found at $SKILL_PATH"
    exit 1
fi

chmod +x "$SKILL_PATH"
echo "[setup] format_gw.py is executable."

echo "[setup] Verifying format-rules.md exists..."
RULES_PATH="/root/.npm-global/lib/node_modules/openclaw/skills/doc-format-gw/references/format-rules.md"
if [ ! -f "$RULES_PATH" ]; then
    echo "[setup] ERROR: format-rules.md not found"
    exit 1
fi
echo "[setup] format-rules.md found."

echo "[setup] Setup complete."