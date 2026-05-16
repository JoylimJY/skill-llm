#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace/skills/
chmod -R 755 /workspace/tasks/
chmod -R 755 /workspace/memory/

# Make JS stubs executable
find /workspace/skills -name "*.js" -exec chmod +x {} \;

echo "Setup complete."