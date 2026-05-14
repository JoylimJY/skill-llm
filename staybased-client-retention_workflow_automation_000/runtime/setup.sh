#!/bin/bash
set -e

# Ensure artifacts directory exists and is writable
mkdir -p /workspace/workspace/artifacts
chmod -R 755 /workspace/workspace/

echo "Setup complete. Workspace ready."
echo "Client data available at /workspace/workspace/clients/alfreds_plumbing/"
echo "Artifacts output directory: /workspace/workspace/artifacts/"