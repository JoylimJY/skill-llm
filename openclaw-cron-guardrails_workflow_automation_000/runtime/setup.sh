#!/bin/bash
set -e

cd /workspace

# Make all scripts executable
chmod +x scripts/*.py

# Verify the key input file exists
if [ ! -f "jobs/drafts/broken_intent.json" ]; then
    echo "ERROR: broken_intent.json not found" >&2
    exit 1
fi

echo "Setup complete. Workspace contents:"
find /workspace -type f | sort

echo ""
echo "Key test input (broken intent):"
cat jobs/drafts/broken_intent.json