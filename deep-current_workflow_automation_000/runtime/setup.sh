#!/usr/bin/env bash
set -e

# Ensure the CLI script is executable
chmod +x /workspace/scripts/deep-current.py

# Verify the CLI works
python3 /workspace/scripts/deep-current.py list

echo "Setup complete."