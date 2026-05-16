#!/bin/bash
set -e

# Ensure plans directory exists and is writable
mkdir -p /workspace/plans
chmod 755 /workspace/plans

# Ensure logs directory is writable
mkdir -p /workspace/logs
chmod 755 /workspace/logs

echo "Setup complete. Workspace ready at /workspace"