#!/bin/bash
set -e

# Ensure skill scripts are executable
chmod +x /root/.agents/skills/notes-skill/scripts/init.py
chmod +x /root/.agents/skills/notes-skill/scripts/backup.py

# Verify python3 is available
python3 --version

echo "Setup complete."