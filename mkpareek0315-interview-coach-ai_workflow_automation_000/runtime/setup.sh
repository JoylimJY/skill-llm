#!/bin/bash
set -e

# Ensure the workspace has correct permissions
chmod -R 755 /workspace

# Create the home directory structure that the skill expects to exist
# The skill's first-run setup creates ~/.openclaw/interview-coach/
# but we do NOT pre-create it — the agent must do that as part of setup

echo "Setup complete. Workspace ready at /workspace"
echo "Agent must read /workspace/session_briefing.txt and populate the interview-coach data files."