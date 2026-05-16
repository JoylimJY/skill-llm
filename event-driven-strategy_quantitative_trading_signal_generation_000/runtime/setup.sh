#!/usr/bin/env bash
set -e

echo "=== Setup: verifying workspace structure ==="
ls /workspace/data/raw/events/
ls /workspace/data/raw/analyst_reports/

# Make any utility scripts executable
find /workspace/scripts -name "*.py" -exec chmod +x {} \;

echo "=== Setup complete ==="