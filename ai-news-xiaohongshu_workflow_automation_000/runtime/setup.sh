#!/bin/bash
set -e

echo "=== Setting up ai-news-xiaohongshu skill environment ==="

# Make scripts executable
chmod +x /root/.openclaw/workspace/skills/ai-news-xiaohongshu/scripts/create-xiaohongshu-content.js
chmod +x /root/.openclaw/workspace/skills/ai-news-xiaohongshu/scripts/run-full-flow.js

# Verify Node.js is available
node --version
echo "Node.js ready."

# Verify the workspace structure
echo "Skill directory contents:"
ls -la /root/.openclaw/workspace/skills/ai-news-xiaohongshu/

echo "Scripts:"
ls -la /root/.openclaw/workspace/skills/ai-news-xiaohongshu/scripts/

echo "Raw news input available at /workspace/raw_news_input.json"
echo "=== Setup complete ==="