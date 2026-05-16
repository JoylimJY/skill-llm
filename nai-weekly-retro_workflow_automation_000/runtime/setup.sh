#!/bin/bash
set -e

# Make all scripts executable
chmod +x /workspace/scripts/gather_week.py
chmod +x /workspace/scripts/analyze.py
chmod +x /workspace/scripts/retrospective.py
chmod +x /workspace/scripts/history.py
chmod +x /workspace/scripts/cleanup.py

# Ensure the vault directories exist
mkdir -p /workspace/vault/weekly-retro
mkdir -p /workspace/vault/retro-history

# Ensure memory logs are readable
chmod -R a+r /workspace/memory/

echo "Setup complete. Workspace ready."
echo "Memory logs available at: /workspace/memory/game-dev/"
echo "Target sprint: 2024-03-11 to 2024-03-17"