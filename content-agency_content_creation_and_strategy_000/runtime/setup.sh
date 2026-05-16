#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying workspace structure..."
ls /workspace/internal/briefs/2024/

echo "Setup complete. Agent workspace is ready."