#!/bin/bash
set -e

# Ensure the check_state.sh script is executable
chmod +x /root/.openclaw/skills/metacognition/scripts/check_state.sh

# Ensure workspace dirs exist
mkdir -p /home/node/.openclaw/workspace
mkdir -p /root/.openclaw/skills/metacognition/templates
mkdir -p /root/.openclaw/skills/metacognition/scripts

# Verify templates are in place
echo "Templates available:"
ls /root/.openclaw/skills/metacognition/templates/

echo "Scripts available:"
ls /root/.openclaw/skills/metacognition/scripts/

echo "Setup complete."