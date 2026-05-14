#!/bin/bash
set -e

# Ensure scripts are executable
chmod +x /workspace/scripts/journal.py

# Ensure the home .openclaw directory is clean (no pre-existing state)
rm -rf ~/.openclaw/workspace/ops-journal

echo "Setup complete. Journal state is clean."
echo "Workspace contents:"
ls /workspace/scripts/