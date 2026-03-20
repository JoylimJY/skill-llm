#!/bin/bash
set -e

# Make scripts executable if they exist
if [ -d "scripts" ]; then
    chmod +x scripts/*.sh
fi

# Ensure pnpm is available
which pnpm || npm install -g pnpm

echo "Setup complete"