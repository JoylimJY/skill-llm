#!/usr/bin/env bash
set -e

chmod +x /workspace/send_dm.sh
chmod +x /workspace/scripts/game-engine.mjs

# Verify node can run the engine
node /workspace/scripts/game-engine.mjs help > /dev/null 2>&1 || true

echo "Setup complete."