#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying brand brief exists..."
if [ -f "/workspace/brand_brief.json" ]; then
    echo "brand_brief.json found."
else
    echo "ERROR: brand_brief.json missing!"
    exit 1
fi

echo "Setup complete."