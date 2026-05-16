#!/bin/bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace

# Verify the main script file exists
if [ -f "/workspace/production/scripts/script_v2.3.txt" ]; then
    echo "Main script file confirmed at /workspace/production/scripts/script_v2.3.txt"
else
    echo "ERROR: Main script file not found!"
    exit 1
fi

echo "Setup complete. Workspace ready for agent."