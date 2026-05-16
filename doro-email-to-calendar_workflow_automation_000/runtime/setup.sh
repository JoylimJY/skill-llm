#!/bin/bash
set -e

SCRIPTS_DIR="$HOME/.openclaw/workspace/skills/email-to-calendar/scripts"

# Scripts are already made executable by gen_inputs_script via Python chmod.
# Attempt chmod only if we have permission (ignore errors gracefully).
for script in "$SCRIPTS_DIR"/*.sh; do
    chmod +x "$script" 2>/dev/null || true
done

echo "Scripts made executable."
echo "Mock state directory: $HOME/.openclaw/workspace/mock_state/"
echo "Email to process: msg_4a7f9c2b1d8e3f56 (at $HOME/emails/inbox/msg_4a7f9c2b1d8e3f56.json)"