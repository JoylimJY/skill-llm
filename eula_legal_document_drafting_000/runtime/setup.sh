#!/usr/bin/env bash
set -e

chmod +x /workspace/scripts/script.sh

# Verify the script runs
/workspace/scripts/script.sh version

echo "Setup complete."