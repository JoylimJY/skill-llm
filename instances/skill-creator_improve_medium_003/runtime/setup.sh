#!/bin/bash
set -e

# Make scripts executable
chmod +x *.py

# Verify skill structure exists
if [ ! -d "analytics-helper" ]; then
    echo "Error: analytics-helper directory not found"
    exit 1
fi

echo "Setup complete - ready for skill improvement task"