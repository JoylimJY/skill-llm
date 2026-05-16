#!/bin/bash
set -e

# Make the diet logger script executable
chmod +x /home/user/workspace/.openclaw/workspace/skills/diet-logger/scripts/log_diet.py

# Set HOME so the agent can find the skill at ~/.openclaw
export HOME=/home/user

# Create symlink so ~/.openclaw points to workspace
if [ ! -e /home/user/.openclaw ]; then
    ln -s /home/user/workspace/.openclaw /home/user/.openclaw
fi

echo "✅ Setup complete. HOME=$HOME"
echo "   Script path: ~/.openclaw/workspace/skills/diet-logger/scripts/log_diet.py"