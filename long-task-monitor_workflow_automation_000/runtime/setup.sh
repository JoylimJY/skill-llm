#!/bin/bash
set -e

# Ensure the long-task.js is executable in both locations
chmod +x /root/.openclaw/workspace/skills/long-task-monitor/long-task.js

# Ensure workspace symlink exists and is valid
if [ -L /workspace/long-task.js ] && [ -f /workspace/long-task.js ]; then
    echo "Symlink OK"
else
    ln -sf /root/.openclaw/workspace/skills/long-task-monitor/long-task.js /workspace/long-task.js
fi

# Verify Node.js is available
node --version

# Pre-create the long-tasks base directory just in case
mkdir -p /root/.openclaw/workspace/long-tasks

echo "Setup complete."