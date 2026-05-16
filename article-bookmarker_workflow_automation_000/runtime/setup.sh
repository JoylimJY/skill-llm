#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${WORKSPACE_DIR:-/workspace}"

# Ensure scripts are executable
chmod +x "$WORKSPACE/scripts/bookmark.sh"

# Configure git (needed if bookmark.sh or agent tries git operations)
git config --global user.email "agent@benchmark.local"
git config --global user.name "Benchmark Agent"
git config --global init.defaultBranch main

# Export environment variables that the skill requires
# (The agent should discover these from SKILL.md and config/env_reference.txt)
export ARTICLE_BOOKMARK_DIR="/workspace/bookmarks"
export ARTICLE_BOOKMARK_GITHUB="https://github.com/medteam/research-bookmarks"

# Write them to /etc/environment so sub-shells can read them
echo "ARTICLE_BOOKMARK_DIR=/workspace/bookmarks" >> /etc/environment
echo "ARTICLE_BOOKMARK_GITHUB=https://github.com/medteam/research-bookmarks" >> /etc/environment

# Also write to a shell rc so bash sub-processes inherit
cat >> /etc/bash.bashrc <<'EOF'
export ARTICLE_BOOKMARK_DIR="/workspace/bookmarks"
export ARTICLE_BOOKMARK_GITHUB="https://github.com/medteam/research-bookmarks"
EOF

echo "Setup complete. ARTICLE_BOOKMARK_DIR=$ARTICLE_BOOKMARK_DIR"