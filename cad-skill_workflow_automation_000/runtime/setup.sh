#!/bin/bash
set -e

# Make skill_runner.py executable
chmod +x /workspace/skill_runner.py

# Verify the mock runner works with a basic sanity check
echo "Verifying skill_runner.py is operational..."
RESULT=$(python3 /workspace/skill_runner.py '{"skill": "get_running_apps", "args": {}}')
echo "Runner check result: $RESULT"

echo "Setup complete. Workspace ready."
ls /workspace/