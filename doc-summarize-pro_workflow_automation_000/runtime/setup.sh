#!/usr/bin/env bash
set -euo pipefail

# Make the skill script executable
chmod +x /workspace/scripts/script.sh

# Ensure the tool config directory is reset (no pre-existing config)
rm -rf "$HOME/.doc-summarize-pro"

echo "Setup complete. Script is executable, config directory cleared."