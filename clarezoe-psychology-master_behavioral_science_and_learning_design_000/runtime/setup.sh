#!/usr/bin/env bash
set -e

WORKSPACE="${WORKSPACE:-/workspace}"

# Make all scripts executable
chmod +x "$WORKSPACE/scripts/learner_assessment.py"
chmod +x "$WORKSPACE/scripts/conversion_audit.py"
chmod +x "$WORKSPACE/scripts/bias_detector.py"
chmod +x "$WORKSPACE/scripts/search.py"

echo "Setup complete. Scripts are executable."
echo "Workspace contents:"
find "$WORKSPACE" -type f | sort