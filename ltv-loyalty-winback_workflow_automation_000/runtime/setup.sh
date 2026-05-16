#!/bin/bash
set -e

echo "Setting up workspace..."

# Ensure workspace directory is accessible
chmod -R 755 /workspace

echo "Setup complete. Workspace ready."
ls -la /workspace/data/customers/