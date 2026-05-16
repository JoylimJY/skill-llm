#!/usr/bin/env bash
set -e

echo "=== Setting up workspace ==="

# Make the auto-test-generator executable
chmod +x /workspace/skills/auto-test-generator/index.js

# Make the data-formatter executable
chmod +x /workspace/skills/data-formatter/index.js

# Make distractor scripts executable
for f in /workspace/scripts/*.sh; do
  chmod +x "$f"
done

# Verify no test.js exists yet for data-formatter
if [ -f /workspace/skills/data-formatter/test.js ]; then
  echo "ERROR: test.js should not pre-exist for data-formatter"
  exit 1
fi

echo "=== Setup complete ==="
echo "Workspace tree (skills):"
ls -la /workspace/skills/