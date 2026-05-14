#!/bin/bash
set -e

WORKSPACE="${WORKSPACE:-/workspace}"

# Make ops scripts executable
chmod +x "$WORKSPACE/ops/scripts/restart.sh" 2>/dev/null || true

# Ensure ehr_volume is readable (not write-accessible, to match the log error)
chmod 555 "$WORKSPACE/pipeline/mounts/ehr_volume" 2>/dev/null || true

echo "Setup complete."