#!/bin/bash
set -e

# Ensure start.sh is executable
chmod +x /home/devuser/workspace/night-patch/start.sh

# Ensure devuser owns everything relevant
chown -R devuser:devuser /home/devuser/

# Create logs directory under night-patch (owned by devuser)
mkdir -p /home/devuser/workspace/night-patch/logs
chown -R devuser:devuser /home/devuser/workspace/night-patch/logs

echo "Setup complete."