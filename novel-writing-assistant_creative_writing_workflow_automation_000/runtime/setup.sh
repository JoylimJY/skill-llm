#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace/project_xianxia/

echo "Verifying key input file..."
if [ -f "/workspace/project_xianxia/commission_brief.md" ]; then
    echo "Commission brief found."
else
    echo "ERROR: Commission brief missing!"
    exit 1
fi

echo "Setup complete. Agent workspace ready."
echo "Directory structure:"
tree /workspace/project_xianxia/ 2>/dev/null || find /workspace/project_xianxia -type f | sort