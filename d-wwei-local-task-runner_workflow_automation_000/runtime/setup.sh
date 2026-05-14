#!/usr/bin/env bash
set -e

# Ensure the runner is executable
chmod +x /workspace/skills/local-task-runner/index.js

# Verify commander is installed for the runner
cd /workspace/skills/local-task-runner
if [ ! -d node_modules/commander ]; then
    npm install commander > /dev/null 2>&1
fi
cd /workspace

echo "Setup complete. Runner ready at skills/local-task-runner/index.js"