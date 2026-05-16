#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace/

echo "Verifying problem file exists..."
if [ -f "/workspace/media_team/briefs/approved/wok_seasoning_raw_notes.txt" ]; then
    echo "Problem file confirmed."
else
    echo "ERROR: Problem file missing!"
    exit 1
fi

echo "Setup complete."