#!/bin/bash
set -e

echo "Setting up workspace..."

# Ensure workspace permissions
chmod -R 755 /workspace

echo "Workspace ready."
echo "Task brief available at: /workspace/task_brief.md"