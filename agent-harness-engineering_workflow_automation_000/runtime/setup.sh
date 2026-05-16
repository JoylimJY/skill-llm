#!/usr/bin/env bash
set -e

chmod +x /workspace/scripts/bootstrap_project.py

# Ensure repo scripts are executable
chmod +x /workspace/payflow-repo/scripts/run_migrations.sh 2>/dev/null || true

echo "Setup complete. Workspace ready."
echo "Skill bootstrap: /workspace/scripts/bootstrap_project.py"
echo "Target repo:     /workspace/payflow-repo"