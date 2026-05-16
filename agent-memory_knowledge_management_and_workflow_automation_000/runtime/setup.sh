#!/usr/bin/env bash
set -e

# Ensure workspace src is importable
export PYTHONPATH="/workspace:${PYTHONPATH}"
echo "PYTHONPATH set to /workspace"

# Create the target output directory
mkdir -p /workspace/projects/constellation

echo "Setup complete."