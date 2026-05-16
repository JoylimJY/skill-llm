#!/bin/bash
set -e

# Make any existing shell scripts executable
find /workspace -name "*.sh" -exec chmod +x {} \;

echo "Setup complete."