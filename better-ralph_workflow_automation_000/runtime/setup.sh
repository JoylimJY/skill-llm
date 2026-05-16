#!/bin/bash
set -e

# Ensure node is available
node --version
npm --version

# Make tool scripts executable
chmod +x /workspace/scripts/clean.sh

# Verify the workspace git repo is clean
cd /workspace
git status

echo "Setup complete. Current branch: $(git branch --show-current)"
echo "Current prd.json stories:"
cat /workspace/prd.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
for s in data['userStories']:
    print(f'  {s[\"id\"]} priority={s[\"priority\"]} passes={s[\"passes\"]} title={s[\"title\"][:50]}')
"