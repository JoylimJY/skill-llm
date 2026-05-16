#!/bin/bash
set -e

# Ensure all skill scripts are executable
chmod +x ~/.openclaw/workspace/skills/lel-mail/scripts/*.sh
chmod +x ~/.openclaw/workspace/skills/lel-mail/scripts/*.py

# Ensure config directory exists (but NOT the config file itself - agent must create it)
mkdir -p ~/.config/lel-mail

# Ensure queue directory is in place
mkdir -p ~/.openclaw/workspace/skills/lel-mail/queue

echo "Setup complete. Skill scripts are ready."
echo "Config file does NOT exist yet - agent must create it."
ls -la ~/.openclaw/workspace/skills/lel-mail/scripts/
echo "Current queue contents:"
ls -la ~/.openclaw/workspace/skills/lel-mail/queue/