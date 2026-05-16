#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod +x /workspace/scripts/daily_run.sh 2>/dev/null || true

echo "Verifying data files exist..."
ls -la /workspace/data/

echo "Setup complete."