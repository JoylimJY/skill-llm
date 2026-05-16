#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${WORKSPACE:-/workspace}"

# Make the tool script executable
chmod +x "$WORKSPACE/scripts/script.sh"

# Ensure data directory exists and is writable
mkdir -p "$HOME/.local/share/medication-reminder"

echo "Setup complete. Tool is ready at $WORKSPACE/scripts/script.sh"