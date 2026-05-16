#!/bin/bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace

# Verify the main input file exists
if [ ! -f "/workspace/raw_sales_notes_march2026.txt" ]; then
    echo "ERROR: raw_sales_notes_march2026.txt not found!"
    exit 1
fi

echo "Setup complete. Workspace ready."
echo "Primary input file: /workspace/raw_sales_notes_march2026.txt"
ls -la /workspace/