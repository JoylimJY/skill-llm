#!/bin/bash
set -e

# Ensure correct ownership
chown -R axelhu:axelhu /home/axelhu/.openclaw 2>/dev/null || true

# Create a minimal mock `openclaw` CLI that simulates `openclaw status`
mkdir -p /home/axelhu/.local/bin

cat > /home/axelhu/.local/bin/openclaw << 'EOF'
#!/bin/bash
if [ "$1" = "status" ]; then
    CONFIG="$HOME/.openclaw/openclaw.json"
    if [ ! -f "$CONFIG" ]; then
        echo "ERROR: openclaw.json not found"
        exit 1
    fi
    python3 -c "
import json, sys, os
from pathlib import Path

config_path = Path(os.environ['HOME']) / '.openclaw' / 'openclaw.json'
try:
    with open(config_path) as f:
        cfg = json.load(f)
    agents = cfg.get('agents', {}).get('list', [])
    print(f'OpenClaw v{cfg.get(\"version\", \"?\")}')
    print(f'Loaded agents: {len(agents)}')
    for a in agents:
        ws = Path(a.get('workspace',''))
        status = 'OK' if ws.exists() else 'MISSING_WORKSPACE'
        print(f'  [{status}] {a[\"id\"]} -> {a.get(\"model\",{}).get(\"primary\",\"?\")}')
    allow = cfg.get('agentToAgent', {}).get('allow', [])
    print(f'A2A allow list: {allow}')
    bindings = cfg.get('bindings', [])
    print(f'Bindings: {len(bindings)} configured')
except Exception as e:
    print(f'ERROR reading config: {e}')
    sys.exit(1)
"
else
    echo "Usage: openclaw <status|help>"
fi
EOF

chmod +x /home/axelhu/.local/bin/openclaw
chown axelhu:axelhu /home/axelhu/.local/bin/openclaw

# Ensure ~/.local/bin is on PATH for the axelhu user
echo 'export PATH="$HOME/.local/bin:$PATH"' >> /home/axelhu/.bashrc
echo 'export PATH="$HOME/.local/bin:$PATH"' >> /home/axelhu/.profile

echo "Setup complete. openclaw CLI available at /home/axelhu/.local/bin/openclaw"