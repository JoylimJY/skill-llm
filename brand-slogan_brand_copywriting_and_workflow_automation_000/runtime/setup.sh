#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying key input file exists..."
if [ -f "/workspace/brand_briefs/qingyuantang_brief_v2.3.txt" ]; then
    echo "✓ Brand brief found"
else
    echo "✗ Brand brief missing - re-running gen script"
    exit 1
fi

echo "Creating output directory if needed..."
mkdir -p /workspace/output

echo "Setup complete."