#!/bin/bash
set -e

echo "=== Setting up Memory Palace sandbox ==="

# Create the openclaw skills directory structure as if the skill is installed
mkdir -p ~/.openclaw/workspace/skills/memory-palace

# Create a minimal skill manifest so it looks installed
cat > ~/.openclaw/workspace/skills/memory-palace/skill.yaml << 'EOF'
name: memory-palace
version: 1.0
trigger:
  - 记忆宫
  - memory palace
description: 通用记忆激活工具 - 让 AI 成为你的数字分身
EOF

# Ensure workspace permissions
chmod -R 755 /workspace

echo "=== Setup complete ==="
echo "Workspace contents:"
find /workspace -maxdepth 3 -type f | sort