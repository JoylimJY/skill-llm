#!/bin/bash
set -e

echo "=== Setting up workspace ==="

# Run the gen_inputs_script to populate the workspace
python3 /gen_inputs_script.py

# Ensure home openclaw config dir does NOT pre-exist (agent must create it)
rm -rf ~/.openclaw

# Make sure workspace permissions are correct
chmod -R 755 /workspace

echo "=== Setup complete ==="
echo "Workspace contents:"
find /workspace -type f | sort