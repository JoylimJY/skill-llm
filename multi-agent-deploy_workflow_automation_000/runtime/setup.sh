#!/usr/bin/env bash
set -e

# Ensure the deploy script is executable
chmod +x /home/admin/.openclaw/workspace/skills/multi-agent-deploy/scripts/deploy-agent.py

# Ensure the home directory for admin exists (python3 must be accessible)
mkdir -p /home/admin

# Verify the baseline state
echo "=== Sandbox baseline verification ==="
echo "Existing agents:"
ls /home/admin/.openclaw/agents/
echo "Existing workspaces:"
ls /home/admin/.openclaw/ | grep workspace
echo "Config agents:"
python3 -c "
import json, pathlib
cfg = json.loads(pathlib.Path('/home/admin/.openclaw/openclaw.json').read_text())
for a in cfg['agents']:
    print('  -', a['id'])
"
echo "=== Ready for agent task ==="