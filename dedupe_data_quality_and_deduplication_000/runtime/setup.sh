#!/usr/bin/env bash
set -e

# Ensure the skill script is executable
chmod +x /workspace/scripts/script.sh 2>/dev/null || true

# Create the dedupe data directory the skill expects
mkdir -p ~/.dedupe/

echo "Setup complete."