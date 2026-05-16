#!/bin/bash
set -e

# Make the Node.js scripts executable
chmod +x /workspace/skills/daily-fun-content/scripts/generate.mjs
chmod +x /workspace/skills/daily-fun-content/scripts/get-content.mjs

# Verify Node.js is available
node --version

echo "Setup complete. Node.js scripts are ready."
echo "Cache directory exists but daily-fun.json is missing:"
ls -la /workspace/skills/daily-fun-content/cache/ 2>/dev/null && echo "(empty)" || echo "cache dir missing"
echo ""
echo "Skill structure:"
find /workspace/skills/daily-fun-content -type f | sort