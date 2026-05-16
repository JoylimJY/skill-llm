#!/bin/bash
set -e

# Ensure markdownlint-cli2 is accessible
markdownlint-cli2 --version || npx markdownlint-cli2 --version

# Make workspace writable
chmod -R 777 /workspace

echo "Setup complete."