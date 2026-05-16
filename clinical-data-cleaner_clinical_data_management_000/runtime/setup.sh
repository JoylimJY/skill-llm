#!/bin/bash
set -e

echo "Setting up workspace..."

# Make scripts executable
chmod +x /workspace/scripts/main.py

# Verify raw data file exists
if [ ! -f /workspace/raw_data/lb_oncology_raw.csv ]; then
    echo "ERROR: raw_data/lb_oncology_raw.csv not found!"
    exit 1
fi

echo "Raw LB data preview:"
head -3 /workspace/raw_data/lb_oncology_raw.csv

echo "Setup complete."