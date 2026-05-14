#!/usr/bin/env bash
set -e

# Ensure the status_server.py is executable
chmod +x /workspace/skills/tidbyt-status/scripts/status_server.py

# Confirm the stale session file is truly old (belt-and-suspenders)
STALE_FILE="$HOME/.openclaw/agents/main/sessions/main.jsonl"
if [ -f "$STALE_FILE" ]; then
    touch -t 202301010000 "$STALE_FILE"
fi

echo "Setup complete. Skill workspace ready at /workspace/skills/tidbyt-status/"
echo "Session directory: $HOME/.openclaw/agents/main/sessions/"
echo "Stale session files aged to simulate >1 hour of inactivity."