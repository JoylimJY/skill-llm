#!/usr/bin/env bash
set -euo pipefail

# Initialize a git repository so bat's --style=changes can show git decorations
cd /workspace
git init -q
git config user.email "audit@company.internal"
git config user.name "Audit Bot"
git add .
git commit -q -m "Initial commit: infrastructure configs"

# Make scripts executable
chmod +x /workspace/infra/deploy/deploy.sh
chmod +x /workspace/scripts/maintenance/cleanup.sh
chmod +x /workspace/scripts/bootstrap/init.sh

echo "Setup complete."