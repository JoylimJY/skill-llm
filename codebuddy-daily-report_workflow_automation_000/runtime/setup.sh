#!/bin/bash
set -e

# Ensure collect.py is executable
SKILL_DIR="$HOME/.codebuddy/skills/daily-report"
chmod +x "$SKILL_DIR/scripts/collect.py"

# Verify the mock script works correctly
echo "[setup] Testing collect.py with --days-ago 2..."
python "$SKILL_DIR/scripts/collect.py" --days-ago 2 | python3 -c "
import json, sys
data = json.load(sys.stdin)
assert len(data['repos']) == 2, f'Expected 2 repos, got {len(data[\"repos\"])}'
assert len(data['agent_sessions']) == 2, f'Expected 2 sessions, got {len(data[\"agent_sessions\"])}'
print('[setup] collect.py --days-ago 2 returns correct data ✓')
"

echo "[setup] Testing collect.py default (today)..."
python "$SKILL_DIR/scripts/collect.py" | python3 -c "
import json, sys
data = json.load(sys.stdin)
assert len(data['repos']) == 0, f'Expected 0 repos for today, got {len(data[\"repos\"])}'
print('[setup] collect.py default returns empty data ✓')
"

echo "[setup] Skill directory contents:"
ls -la "$SKILL_DIR/scripts/"
echo "[setup] Workspace ready."