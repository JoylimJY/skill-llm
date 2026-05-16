#!/bin/bash
set -e

export WORKSPACE="${WORKSPACE:-/workspace}"

# Generate workspace inputs first
python3 /gen_inputs.py

# Ensure scripts are executable
chmod +x "$WORKSPACE/scripts/analyze_memory.py"
chmod +x "$WORKSPACE/scripts/defragment.py"
chmod +x "$WORKSPACE/scripts/verify_memory.py"

echo "Setup complete. Workspace: $WORKSPACE"
echo "Memory files ready for defragmentation."
ls -la "$WORKSPACE/"