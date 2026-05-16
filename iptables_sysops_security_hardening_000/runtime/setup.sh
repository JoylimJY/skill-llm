#!/bin/bash
set -e

# Ensure the skill script is executable
chmod +x /workspace/scripts/script.sh

# Ensure deploy scripts are executable (distractors)
chmod +x /workspace/deploy/staging/deploy.sh 2>/dev/null || true
chmod +x /workspace/deploy/production/deploy.sh 2>/dev/null || true

echo "Setup complete. Workspace ready."
echo "Skill script available at: /workspace/scripts/script.sh"