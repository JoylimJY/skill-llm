#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Setup complete. Workspace is ready."
ls -la /workspace