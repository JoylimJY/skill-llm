#!/usr/bin/env bash
set -e

# Default WORKSPACE if not set
WORKSPACE="${WORKSPACE:-/workspace}"

# Make the analyzer script executable
chmod +x "${WORKSPACE}/scripts/analyze_profile.py"

echo "Setup complete. Workspace is ready."
echo "Artifacts:"
find "${WORKSPACE}/artifacts/run_20240315_bert_large" -type f | sort