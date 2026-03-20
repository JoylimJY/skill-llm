#!/bin/bash
set -e

# Ensure pnpm is available
if ! command -v pnpm &> /dev/null; then
    npm install -g pnpm
fi

# Make scripts executable
chmod +x scripts/*.sh

echo "Setup complete"