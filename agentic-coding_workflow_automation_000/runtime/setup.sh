#!/usr/bin/env bash
set -e

# Ensure the workspace is a git repo (required by the skill's metadata: "requires": {"bins": ["git"]})
cd /workspace
if [ ! -d ".git" ]; then
    git init
    git add -A
    git commit -m "chore: initial legacy logistics codebase"
fi

# Ensure ~/agentic-coding exists and is empty (agent must create required files)
mkdir -p ~/agentic-coding

# Make the test runner clearly accessible
chmod +x /workspace/logistics/tests/unit/test_shipping.py 2>/dev/null || true

echo "Setup complete. Initial git commit created. agentic-coding dir ready."