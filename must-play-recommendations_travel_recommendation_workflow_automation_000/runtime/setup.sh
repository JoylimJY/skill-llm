#!/bin/bash
set -e

# Verify flyai CLI is installed, install if missing
if ! command -v flyai &> /dev/null; then
    echo "Installing flyai CLI..."
    npm install -g @fly-ai/flyai-cli --registry https://registry.npmmirror.com 2>/dev/null || \
    npm install -g @fly-ai/flyai-cli 2>/dev/null || true
fi

# Test if flyai is available
flyai --help > /dev/null 2>&1 && echo "flyai CLI is available" || echo "WARNING: flyai CLI may not be available"

# Ensure workspace permissions
chmod -R 755 /workspace

echo "Setup complete."