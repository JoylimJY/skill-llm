#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying job listing exists..."
if [ -f /workspace/current_job_listing.txt ]; then
    echo "Job listing confirmed at /workspace/current_job_listing.txt"
else
    echo "ERROR: Job listing missing!"
    exit 1
fi

echo "Setup complete."