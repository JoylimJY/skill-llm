#!/bin/bash
set -e

# Make scripts executable
chmod +x /workspace/scripts/notes.js
chmod +x /workspace/scripts/reminders.js

# Ensure data directory exists
mkdir -p /workspace/data

echo "Setup complete. Scripts are ready."
echo "Node version: $(node --version)"