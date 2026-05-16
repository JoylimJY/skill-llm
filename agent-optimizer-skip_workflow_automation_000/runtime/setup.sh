#!/bin/bash
set -e

# Ensure workspace permissions
chmod -R 755 /workspace

# Make any skill scripts executable
find /workspace/skills -name "*.py" -exec chmod +x {} \; 2>/dev/null || true

echo "Setup complete. Workspace ready."
echo "Contents of /workspace/workspace:"
ls /workspace/workspace/ 2>/dev/null || echo "(empty)"