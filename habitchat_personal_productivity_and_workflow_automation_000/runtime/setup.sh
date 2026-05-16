#!/usr/bin/env bash
set -e

# Make all scripts executable
chmod +x /workspace/skills/habitchat/scripts/habit_tracker.py
chmod +x /workspace/skills/habitchat/scripts/reminder.py
chmod +x /workspace/skills/habitchat/scripts/coach.py

echo "Setup complete. Skill scripts are executable."
echo "Skill base directory: /workspace/skills/habitchat"
echo "Scripts directory:    /workspace/skills/habitchat/scripts"