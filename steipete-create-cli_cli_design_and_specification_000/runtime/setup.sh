#!/usr/bin/env bash
set -e

# Ensure the guidelines file is readable
chmod 644 /workspace/agent-scripts/skills/create-cli/references/cli-guidelines.md

echo "Setup complete. Workspace ready."
echo "Agent should find the guidelines at: agent-scripts/skills/create-cli/references/cli-guidelines.md"