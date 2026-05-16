#!/bin/bash
set -e

# Ensure clawion is installed and accessible
if ! command -v clawion &> /dev/null; then
    echo "clawion not found via npm global, attempting install..."
    npm install -g clawion
fi

# Verify installation
clawion --help > /dev/null 2>&1 && echo "clawion CLI is available." || echo "WARNING: clawion CLI not found after install attempt."

# Ensure workspace directory is writable
chmod -R 755 /workspace

echo "Setup complete."