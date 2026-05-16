#!/bin/bash
set -e

chmod +x /workspace/scripts/build_marine_plan.py

# Verify key reference files exist
for f in \
    /workspace/references/watch-models.md \
    /workspace/references/safety-anchors.md \
    /workspace/references/internet-budgeting.md \
    /workspace/scripts/build_marine_plan.py; do
  if [ ! -f "$f" ]; then
    echo "ERROR: Missing required file: $f"
    exit 1
  fi
done

echo "Setup complete. Workspace ready."