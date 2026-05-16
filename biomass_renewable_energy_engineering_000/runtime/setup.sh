#!/usr/bin/env bash
set -e

WORKSPACE="${WORKSPACE:-/workspace}"

# Make the skill script executable
chmod +x "$WORKSPACE/scripts/script.sh"

echo "Setup complete. Skill script is ready at: $WORKSPACE/scripts/script.sh"