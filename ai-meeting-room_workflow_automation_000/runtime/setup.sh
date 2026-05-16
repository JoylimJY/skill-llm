#!/bin/bash
set -e

echo "Setting up AI Meeting Room evaluation environment..."

# Ensure workspace permissions
chmod -R 755 /workspace

echo "Setup complete. Workspace ready."
echo "Agent should generate: meeting_report.md"