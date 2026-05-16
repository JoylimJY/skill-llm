#!/bin/bash
set -e

# Ensure obsidian-cli is executable and on PATH
chmod +x /workspace/obsidian-cli
cp /workspace/obsidian-cli /usr/local/bin/obsidian-cli
chmod +x /usr/local/bin/obsidian-cli

# Install pyyaml if not already present (needed by the mock CLI)
pip install pyyaml -q -i https://pypi.tuna.tsinghua.edu.cn/simple

# Verify the mock CLI works
obsidian-cli print-default 2>/dev/null || echo "No default vault set yet (expected)"

echo "Setup complete. obsidian-cli is ready."