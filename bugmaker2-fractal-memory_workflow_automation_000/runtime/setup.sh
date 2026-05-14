#!/bin/bash
set -e

# Make all scripts executable
chmod +x /workspace/scripts/*.py

echo "Setup complete. Workspace ready."
echo "Flat daily files in /workspace/memory/:"
ls /workspace/memory/
echo ""
echo "Scripts available:"
ls /workspace/scripts/
echo ""
echo "Assets available:"
ls /workspace/assets/