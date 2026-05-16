#!/bin/bash
set -e

# Ensure output directory exists and is writable
mkdir -p /mnt/user-data/outputs
chmod 777 /mnt/user-data/outputs
chmod 777 /mnt/user-data/uploads

echo "Workspace initialized."
echo "Input file: /mnt/user-data/uploads/pharmacy_dispense_2024.csv"
echo "Output directory: /mnt/user-data/outputs/"