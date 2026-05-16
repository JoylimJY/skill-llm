#!/usr/bin/env bash
set -e

chmod +x /workspace/scripts/game_manager.py

# Verify the game_manager loads cleanly
cd /workspace
python scripts/game_manager.py load > /dev/null

echo "Setup complete. Game engine is ready."