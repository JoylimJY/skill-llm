#!/usr/bin/env bash
set -e

# Make the lottery script executable
chmod +x /workspace/scripts/script.sh

# Ensure storage directory exists
mkdir -p "$HOME/.local/share/lottery"

echo "Setup complete. Lottery script is ready at /workspace/scripts/script.sh"