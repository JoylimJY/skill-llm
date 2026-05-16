#!/bin/bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace

echo "Setup complete. Workspace ready."
echo "Agent should read /workspace/SKILL.md and /workspace/projects/aurora/briefs/friction_brief.txt"