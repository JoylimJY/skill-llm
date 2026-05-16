#!/bin/bash
set -e

# Ensure scripts directory is importable
cd /workspace
export PYTHONPATH="/workspace:$PYTHONPATH"

# Create the cortexgraph config directory
mkdir -p ~/.config/cortexgraph

# Make scripts importable
touch /workspace/scripts/__init__.py 2>/dev/null || true

echo "Setup complete. PYTHONPATH=$PYTHONPATH"