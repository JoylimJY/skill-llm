#!/usr/bin/env bash
set -euo pipefail

HOME_DIR=$(eval echo "~")
SKILL_SCRIPT="$HOME_DIR/.openclaw/workspace/skills/dashboard-theme/change-theme.sh"

# Ensure the skill script is executable
chmod +x "$SKILL_SCRIPT"

echo "✅ Setup complete. Skill script ready at $SKILL_SCRIPT"
echo "   OpenClaw UI assets: $HOME_DIR/.openclaw/ui/dist/assets/"
ls "$HOME_DIR/.openclaw/ui/dist/assets/"