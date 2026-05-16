#!/bin/bash
set -e

# Ensure workspace is the cwd
cd /workspace

# Make any helper scripts executable
find /workspace/scripts -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true

echo "Setup complete."