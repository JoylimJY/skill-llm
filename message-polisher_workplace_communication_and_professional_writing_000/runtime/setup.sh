#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying raw draft exists..."
if [ -f "/workspace/projects/internal_comms/raw_draft_pm_wang_fang.txt" ]; then
    echo "✓ Raw draft file found"
else
    echo "✗ ERROR: Raw draft file missing!"
    exit 1
fi

echo "Setup complete. Workspace is ready."