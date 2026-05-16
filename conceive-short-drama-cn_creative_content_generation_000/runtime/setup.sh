#!/bin/bash
set -e

echo "Setting up workspace..."

# Ensure output directory exists and is writable
mkdir -p /workspace/output/pending
chmod -R 777 /workspace/output
chmod -R 777 /workspace/projects

echo "Setup complete. Agent should find the creative brief and produce story_outline.txt"