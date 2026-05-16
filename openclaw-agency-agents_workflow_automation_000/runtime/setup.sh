#!/usr/bin/env bash
set -euo pipefail

SKILL_BASE="$HOME/.openclaw/workspace/skills/openclaw-agency-agents"
SCRIPTS_DIR="$SKILL_BASE/scripts"

# Ensure all scripts are executable (belt-and-suspenders)
chmod +x "$SCRIPTS_DIR/setup.sh"
chmod +x "$SCRIPTS_DIR/activate.sh"
chmod +x "$SCRIPTS_DIR/list.sh"
chmod +x "$SCRIPTS_DIR/search.sh"
chmod +x "$SCRIPTS_DIR/restore.sh"
chmod +x "$SCRIPTS_DIR/update.sh"

echo "[sandbox] All scripts are executable."
echo "[sandbox] Active config state before agent begins:"
if [ -f "$SKILL_BASE/active_agent.conf" ]; then
    cat "$SKILL_BASE/active_agent.conf"
else
    echo "(active_agent.conf not yet created — setup.sh has not been run)"
fi
echo "[sandbox] Ready for agent."