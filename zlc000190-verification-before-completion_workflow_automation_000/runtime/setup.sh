#!/usr/bin/env bash
set -e

chmod +x /workspace/scripts/build.sh

# Verify the workspace is consistent (sanity check for setup, not for agent)
cd /workspace
python -m pytest tests/unit -q --tb=no 2>&1 | tail -3
echo "Setup complete."