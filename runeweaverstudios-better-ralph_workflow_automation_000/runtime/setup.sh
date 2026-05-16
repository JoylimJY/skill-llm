#!/bin/bash
set -e

cd /workspace

# Ensure scripts are executable
chmod +x scripts/build.sh scripts/deploy.sh 2>/dev/null || true
chmod +x src/cli.js 2>/dev/null || true

# Confirm we are on main branch
git branch --show-current

# Show current state for debugging
echo "=== prd.json stories ==="
python3 -c "
import json
with open('prd.json') as f:
    prd = json.load(f)
for s in prd['userStories']:
    print(f\"  {s['id']} priority={s['priority']} passes={s['passes']} - {s['title']}\")
"

echo "=== npm test (should fail - US-001 not implemented yet) ==="
npm test 2>&1 | tail -5 || echo "(expected failure - --version not yet implemented)"

echo "=== Setup complete. Agent should run Better Ralph iteration. ==="