#!/bin/bash
set -e

echo "Setting up Argus Edge evaluation sandbox..."

# Ensure workspace directories exist
mkdir -p /workspace/data/processed
mkdir -p /workspace/reports/daily

# Make scripts executable if any exist
find /workspace/scripts -name "*.py" -exec chmod +x {} \; 2>/dev/null || true
find /workspace/scripts -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true

echo "Setup complete."