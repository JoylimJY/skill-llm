#!/usr/bin/env bash
set -e

# Make skill_manager.py executable
chmod +x /root/.openclaw/workspace/skills/dynamic-skill-manager/scripts/skill_manager.py

# Verify structure
echo "=== Workspace Structure ==="
find /root/.openclaw/workspace -maxdepth 3 -type f | sort | head -40

echo "=== Registry snapshot ==="
cat /root/.openclaw/workspace/.skill-manager/registry.json | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Skills in registry: {list(d[\"skills\"].keys())}')"

echo "=== Skills on disk ==="
ls /root/.openclaw/workspace/skills/

echo "Setup complete."