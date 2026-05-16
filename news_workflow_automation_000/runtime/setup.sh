#!/bin/bash
set -e

# Ensure ~/news/ directory exists and has correct permissions
mkdir -p ~/news
chmod 755 ~/news
chmod 644 ~/news/memory.md ~/news/history.md ~/news/sources.md 2>/dev/null || true

# Ensure workspace scripts are executable
chmod +x /workspace/tools/scripts/word_count.sh 2>/dev/null || true
chmod +x /workspace/tools/scripts/format_citations.py 2>/dev/null || true

echo "Setup complete. Workspace ready."
echo "Agent should read /workspace/my_news_preferences.txt and ~/news/ contents."