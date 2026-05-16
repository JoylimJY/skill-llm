#!/bin/bash
set -e

# Ensure the analyze-user.py is executable
chmod +x /workspace/.openclaw/workspace/skills/openclaw-boss/scripts/analyze-user.py
chmod +x /workspace/.openclaw/workspace/skills/openclaw-boss/scripts/weekly-profile.sh
chmod +x /workspace/.openclaw/workspace/skills/openclaw-boss/scripts/monthly-profile.sh

# Ensure reports directory exists
mkdir -p /workspace/.openclaw/workspace/reports

echo "Setup complete. Script is ready at:"
echo "  /workspace/.openclaw/workspace/skills/openclaw-boss/scripts/analyze-user.py"