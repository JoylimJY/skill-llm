#!/bin/bash
set -e

# Make scripts executable
find /workspace/biotech_intel/scripts -name "*.py" -exec chmod +x {} \;

# Verify primary data file exists
if [ ! -f /workspace/biotech_intel/raw_data/resistance_surveillance_2018_2023.csv ]; then
    echo "ERROR: Primary data file not found!"
    exit 1
fi

echo "Workspace setup complete."
echo "Files in workspace:"
find /workspace/biotech_intel -type f | sort