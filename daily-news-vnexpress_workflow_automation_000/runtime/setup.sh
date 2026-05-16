#!/bin/bash
set -e

echo "=== Setting up VNExpress News Skill environment ==="

# Install skill dependencies
cd /workspace/skills/daily-news-vnexpress
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --quiet

# Make main.py executable
chmod +x /workspace/skills/daily-news-vnexpress/main.py

echo "=== Setup complete ==="
echo "Skill directory: /workspace/skills/daily-news-vnexpress"
echo "main.py is ready."