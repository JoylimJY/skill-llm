#!/bin/bash
set -e

echo "Setting up workspace..."

# Ensure workspace directory permissions are correct
chmod -R 755 /workspace

echo "Setup complete. Workspace is ready."
ls -la /workspace/