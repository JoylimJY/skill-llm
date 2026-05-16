#!/bin/bash
set -e

# Make any shell scripts executable
find /workspace -name "*.sh" -exec chmod +x {} \;

echo "Setup complete."