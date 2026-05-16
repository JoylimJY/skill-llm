#!/bin/bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace

# Verify snipgrapher is installed and accessible
echo "Verifying snipgrapher installation..."
snipgrapher --version || npx --yes snipgrapher --version

echo "Setup complete. Workspace is ready."