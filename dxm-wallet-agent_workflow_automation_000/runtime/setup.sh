#!/usr/bin/env bash
set -e

# Make all scripts executable
chmod +x /workspace/scripts/sp-weather-cli.js
chmod +x /workspace/scripts/qrcode.js
chmod +x /workspace/scripts/tools.js

# Ensure qrcodes output directory exists
mkdir -p /workspace/qrcodes

# Verify node is available
node --version

echo "Setup complete."