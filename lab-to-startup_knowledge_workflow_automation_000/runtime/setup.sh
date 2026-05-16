#!/bin/bash
set -e

echo "Setting up workspace..."

# Ensure workspace permissions
chmod -R 755 /workspace

# Verify the project brief exists
if [ -f "/workspace/project_brief.txt" ]; then
    echo "Project brief found: /workspace/project_brief.txt"
else
    echo "ERROR: project_brief.txt not found"
    exit 1
fi

echo "Setup complete. Agent should produce advisory_report.json in the workspace."