#!/usr/bin/env bash
set -e

WORKSPACE="/workspace"

# Ensure generate.sh is executable
chmod +x "$WORKSPACE/generate.sh"

# Verify the script is runnable
echo "Setup complete. generate.sh is ready."
ls -la "$WORKSPACE/generate.sh"