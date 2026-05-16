#!/bin/bash
set -e

chmod +x /workspace/scripts/cooldown.py

# Make cooldown.py directly executable as python3 script
chmod 755 /workspace/scripts/cooldown.py

echo "Setup complete. Workspace ready for agent."
echo "Active session data:"
cat /workspace/sessions/active/session_current.json