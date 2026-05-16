#!/bin/bash
set -e

echo "Setting up workspace..."
chmod -R 755 /workspace

# Ensure output directory exists
mkdir -p /workspace/output

echo "Setup complete. Agent should produce: competitive_briefing.md"