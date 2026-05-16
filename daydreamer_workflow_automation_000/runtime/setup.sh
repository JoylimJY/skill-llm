#!/bin/bash
set -e

# Make daydream.py executable
chmod +x /workspace/.claude/skills/daydreamer/daydream.py

# Verify Python is available
python3 --version

# Make sure workspace is writable
chmod -R 777 /workspace

echo "Setup complete. Workspace at /workspace, skill at /workspace/.claude/skills/daydreamer/"
echo "No daydreamer-config.json exists — agent must perform first-install."