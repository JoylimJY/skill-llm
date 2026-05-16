#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying reference files exist..."
ls /workspace/references/templates.md

echo "Setup complete."