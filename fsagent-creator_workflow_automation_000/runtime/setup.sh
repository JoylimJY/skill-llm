#!/bin/bash
set -e

# Ensure scripts are executable
chmod +x /home/admin/create-agent.sh
chmod +x /home/admin/delete-agent.sh
chmod +x /home/admin/list-agents.sh
chmod +x /home/admin/openclaw
chmod +x /usr/local/bin/openclaw

# Fix ownership
chown -R admin:admin /home/admin/.openclaw
chown -R admin:admin /home/admin/

# Verify initial config is valid JSON
python3 -c "
import json
with open('/home/admin/.openclaw/openclaw.json') as f:
    cfg = json.load(f)
assert 'main' in cfg['agents']['list'], 'main agent missing'
print('Initial config OK. Agents:', cfg['agents']['list'])
"

echo "Setup complete. Workspace ready."