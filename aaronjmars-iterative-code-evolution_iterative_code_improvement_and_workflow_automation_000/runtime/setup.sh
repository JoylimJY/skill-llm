#!/bin/bash
set -e

# Make run script executable
chmod +x /workspace/scripts/run_all.sh

# Run initial test suite to establish baseline (capture output, don't fail)
cd /workspace
echo "=== Running baseline tests to confirm broken state ==="
python -m pytest genomics_pipeline/tests/ -v --tb=short 2>&1 | tail -20 || true

echo "=== Workspace ready. Initial test suite shows failures as expected. ==="