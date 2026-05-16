#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace
chmod +x /workspace/scripts/import_data.sh 2>/dev/null || true

echo "Setup complete. Workspace ready at /workspace"
ls -la /workspace/