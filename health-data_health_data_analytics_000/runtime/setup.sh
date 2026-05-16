#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${WORKSPACE:-/workspace}"

# Make health-data.sh executable
chmod +x "$WORKSPACE/health-data/health-data.sh"

echo "Setup complete."
echo "health-data.sh is executable."
ls -la "$WORKSPACE/health-data/health-data.sh"