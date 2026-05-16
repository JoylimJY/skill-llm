#!/bin/bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace

# Verify the main problem file exists
if [ ! -f "/workspace/src/game.js" ]; then
    echo "ERROR: game.js not found!"
    exit 1
fi

echo "Setup complete. Workspace ready."
echo "Main file to refactor: /workspace/src/game.js"
echo "Target output: /workspace/src/refactored_game.js"