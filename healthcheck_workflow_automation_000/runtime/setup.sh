#!/bin/bash
set -e

# Ensure Node.js is available and working
node --version

# Ensure workspace permissions are correct
chmod -R 755 /workspace

echo "Setup complete. Node.js version: $(node --version)"
echo "Workspace ready at /workspace"