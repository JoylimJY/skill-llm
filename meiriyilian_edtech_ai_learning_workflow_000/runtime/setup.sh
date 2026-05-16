#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying workspace structure..."
ls -la /workspace/
ls -la /workspace/references/

echo "Setup complete."