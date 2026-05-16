#!/bin/bash
set -e

# Ensure build_manifest.sh is executable
chmod +x /workspace/build_manifest.sh

# Ensure results/tables directory exists for output
mkdir -p /workspace/results/tables

# Clear any pre-existing log or manifest to ensure clean state
rm -f /workspace/build_log.txt
rm -f /workspace/results/tables/checksums.md5

echo "Setup complete. Workspace is ready."