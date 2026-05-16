#!/bin/bash
set -e

cd /workspace
git config user.email "dev@fintech-example.local"
git config user.name "Dev Bot"

# Make scripts executable
chmod +x scripts/migrate.sh scripts/seed_dev.py 2>/dev/null || true

echo "Setup complete. Workspace ready."
echo "Git log:"
git log --oneline