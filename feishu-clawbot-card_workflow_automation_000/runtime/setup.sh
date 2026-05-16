#!/usr/bin/env bash
set -e

echo "=== Runtime Setup ==="

cd /workspace

# Ensure skill directory exists and is properly installed
if [ -d "skills/feishu-clawbot-card" ]; then
    echo "Skill directory found: skills/feishu-clawbot-card"
    ls skills/feishu-clawbot-card/
    cd skills/feishu-clawbot-card
    if [ -f "package.json" ]; then
        npm install 2>/dev/null || true
    fi
    cd /workspace
else
    echo "WARNING: Skill directory not found. Attempting clone..."
    mkdir -p skills
    git clone https://github.com/HMyaoyuan/feishu-clawbot-card.git skills/feishu-clawbot-card 2>/dev/null || true
    if [ -d "skills/feishu-clawbot-card" ]; then
        cd skills/feishu-clawbot-card && npm install && cd /workspace
    fi
fi

# Make skill entry point executable if it exists
if [ -f "skills/feishu-clawbot-card/index.js" ]; then
    chmod +x skills/feishu-clawbot-card/index.js
    echo "index.js is executable."
fi

# Ensure output directories exist
mkdir -p ops/registry/exports
mkdir -p ops/registry/imports

echo "=== Setup Complete ==="
echo "Node version: $(node --version)"
echo "Workspace contents:"
ls /workspace/