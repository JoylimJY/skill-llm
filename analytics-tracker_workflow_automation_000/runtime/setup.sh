#!/bin/bash
set -e

# Ensure workspace permissions
chmod -R 755 /workspace

# Verify key input files exist
echo "Verifying input files..."
ls /workspace/analytics/raw_data/
ls /workspace/analytics/raw_data/week_20260216_engagement.json
echo "Setup complete. Agent workspace is ready."