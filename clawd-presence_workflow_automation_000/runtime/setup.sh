#!/bin/bash
set -e

# Make all scripts executable
chmod +x /workspace/scripts/configure.py
chmod +x /workspace/scripts/status.py
chmod +x /workspace/scripts/display.py

echo "Scripts made executable."
echo "Workspace ready."
ls -la /workspace/scripts/