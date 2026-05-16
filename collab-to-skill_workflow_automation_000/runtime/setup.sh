#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying key input file exists..."
if [ ! -f "/workspace/edtech-sprint/sessions/raw/collab_session_2024-03-15.txt" ]; then
    echo "ERROR: Input transcript not found!"
    exit 1
fi

echo "Setup complete. Workspace ready."
tree /workspace 2>/dev/null || find /workspace -type f | sort