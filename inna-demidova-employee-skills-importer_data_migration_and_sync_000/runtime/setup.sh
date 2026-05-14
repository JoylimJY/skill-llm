#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

# Ensure output directories exist
mkdir -p /workspace/hr_system/exports/processed
mkdir -p /workspace/outputs

echo "Setup complete."