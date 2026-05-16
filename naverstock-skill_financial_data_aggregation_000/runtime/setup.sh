#!/bin/bash
set -e

echo "=== Setting up naver-stock skill ==="

# The skill scripts are already in the workspace per SKILL.md convention
# Install the naver-stock package from npm (public registry)
cd /workspace

# Install the naver-stock tool globally or locally
npm install naver-stock 2>/dev/null || true

# Try to locate index.cjs from the skill - it should be available via npx or node_modules
# The SKILL.md says scripts already exist; attempt to set up via npm package
if [ ! -f /workspace/index.cjs ]; then
    # Try finding it in node_modules
    SKILL_CJS=$(find /workspace/node_modules -name "index.cjs" 2>/dev/null | head -1)
    if [ -n "$SKILL_CJS" ]; then
        cp "$SKILL_CJS" /workspace/index.cjs
        echo "Copied index.cjs from node_modules: $SKILL_CJS"
    fi
fi

chmod +x /workspace/scripts/fetch_old.sh /workspace/scripts/cleanup.sh 2>/dev/null || true

echo "=== Setup complete ==="
ls /workspace/