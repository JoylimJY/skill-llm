#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying key input files exist..."
if [ ! -f "/workspace/account_data/account_metrics.csv" ]; then
    echo "ERROR: account_metrics.csv not found"
    exit 1
fi

if [ ! -f "/workspace/content_brief.txt" ]; then
    echo "ERROR: content_brief.txt not found"
    exit 1
fi

echo "Setup complete. Agent workspace is ready."
echo ""
echo "Workspace structure:"
find /workspace -type f | sort