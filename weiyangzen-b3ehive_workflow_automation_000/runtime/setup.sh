#!/bin/bash
set -e

chmod +x /workspace/scripts/benchmark.sh 2>/dev/null || true
chmod +x /workspace/scripts/deploy.sh 2>/dev/null || true

# Ensure workspace directories are accessible
chmod -R 755 /workspace/

echo "Setup complete. Workspace ready for agent."