#!/bin/bash
set -e

# Ensure scripts are executable
chmod +x /workspace/knowledge-sync/scripts/sync-realtime.sh
chmod +x /workspace/knowledge-sync/scripts/git-auto-push.sh
chmod +x /workspace/knowledge-sync/scripts/git-auto-pull.sh

# Initialize a local git repo in data/ so git commands won't fail during agent testing
cd /workspace/data
git init
git config user.email "agent@test.local"
git config user.name "Agent Test"
git add -A
git commit -m "initial commit" --allow-empty

echo "Setup complete."