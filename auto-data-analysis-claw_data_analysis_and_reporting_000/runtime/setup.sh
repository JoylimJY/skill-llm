#!/bin/bash
set -e

WORKSPACE="${WORKSPACE:-/workspace}"

chmod +x "$WORKSPACE/scripts/analyze.py"
chmod +x "$WORKSPACE/scripts/report_generator.py"

echo "Setup complete. Scripts are executable."
echo "Workspace contents:"
find "$WORKSPACE" -type f | sort