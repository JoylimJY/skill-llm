#!/bin/bash
set -e

# Copy skill reference files into the workspace so the agent can read them
SKILL_DIR="/workspace/feishu-skill"

# The SKILL.md and references are already mounted/available in the container
# at the path the agent can read. Ensure the workspace is ready.
chmod -R 755 /workspace

echo "Workspace initialized. Agent should read the skill documentation to complete the task."
echo "Key files available:"
ls /workspace/projects/mobile-app-launch/