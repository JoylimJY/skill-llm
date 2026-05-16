#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying input files exist..."
if [ ! -f "/workspace/health_data_2025_jan.txt" ]; then
    echo "ERROR: Primary input file missing!"
    exit 1
fi

echo "Setup complete. Agent workspace ready at /workspace"