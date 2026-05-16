#!/usr/bin/env bash
set -euo pipefail

# Make the official.sh script executable
chmod +x /workspace/scripts/official.sh

# Create output directory if missing
mkdir -p /workspace/output

echo "Setup complete. official.sh is executable."
echo "Workspace contents:"
find /workspace -type f | sort