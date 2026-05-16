#!/bin/bash
set -e

chmod +x /workspace/scripts/apple_notes.py

# Make scripts importable as a package
cd /workspace
export PYTHONPATH="/workspace:$PYTHONPATH"

echo "Setup complete. Workspace ready."
echo "PYTHONPATH set to include /workspace"