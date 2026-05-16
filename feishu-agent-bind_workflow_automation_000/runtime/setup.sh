#!/bin/bash
set -e

HOME_DIR="$HOME"
OPENCLAW_DIR="$HOME_DIR/.openclaw"
DEVOPS_CHAT_ID="oc_d3f4a8b2c1e5f6a7b8c9d0e1"

# Create bin directory for mock openclaw CLI
mkdir -p "$HOME_DIR/bin"

# -------------------------------------------------------------------
# Mock `openclaw` CLI — reads/writes ~/.openclaw/openclaw.json
# -------------------------------------------------------------------
cat > "$HOME_DIR/bin/openclaw" << 'OPENCLAW_SCRIPT'
#!/bin/bash
# Mock openclaw CLI for sandbox testing
OPENCLAW_DIR="$HOME/.openclaw"
CONFIG="$OPENCLAW_DIR/openclaw.json"

cmd="$1"
subcmd="$2"

case "$cmd" in
  config)
    case "$subcmd" in
      get)
        key="$3"
        # Use python to extract nested key via dot notation
        python3 -c "
import json, sys
with open('$CONFIG') as f:
    c = json.load(f)
parts = '$key'.split('.')
val = c
for p in parts:
    val = val[p]
print(json.dumps(val, indent=2, ensure_ascii=False))
"
        ;;
      set)
        # openclaw config set --json <key> '<value>'
        if [ "$3" = "--json" ]; then
          key="$4"
          value="$5"
          python3 -c "
import json, sys, os
with open('$CONFIG') as f:
    c = json.load(f)
parts = '$key'.split('.')
obj = c
for p in parts[:-1]:
    obj = obj.setdefault(p, {})
obj[parts[-1]] = json.loads('''$value''')
with open('$CONFIG', 'w') as f:
    json.dump(c, f, indent=2, ensure_ascii=False)
print('OK')
"
        fi
        ;;
    esac
    ;;
  agents)
    case "$subcmd" in
      add)
        agent_id="$3"
        python3 -c "
import json
with open('$CONFIG') as f:
    c = json.load(f)
existing = [a['id'] for a in c['agents']['list']]
if '$agent_id' not in existing:
    c['agents']['list'].append({'id': '$agent_id', 'name': '$agent_id', 'workspace': '$OPENCLAW_DIR/workspace', 'model': 'gpt-4o'})
    with open('$CONFIG', 'w') as f:
        json.dump(c, f, indent=2, ensure_ascii=False)
    print('Agent $agent_id added.')
else:
    print('Agent $agent_id already exists.')
"
        ;;
      bind)
        # Intentionally broken: sets accountId=<chat_id> (documented pitfall)
        agent_arg=""
        bind_arg=""
        while [[ "$#" -gt 0 ]]; do
          case "$1" in
            --agent) agent_arg="$2"; shift 2 ;;
            --bind) bind_arg="$2"; shift 2 ;;
            *) shift ;;
          esac
        done
        chat_id="${bind_arg#feishu:}"
        python3 -c "
import json
with open('$CONFIG') as f:
    c = json.load(f)
bindings = c.get('bindings', [])
bindings.append({
    'agentId': '$agent_arg',
    'match': {
        'channel': 'feishu',
        'peer': {'kind': 'group', 'id': 'WRONG_PEER'},
        'accountId': '$chat_id'
    }
})
c['bindings'] = bindings
with open('$CONFIG', 'w') as f:
    json.dump(c, f, indent=2, ensure_ascii=False)
print('WARNING: Used broken bind CLI. accountId set to chat_id (incorrect).')
"
        ;;
    esac
    ;;
  sessions)
    import_flag=""
    all_agents=""
    json_flag=""
    while [[ "$#" -gt 0 ]]; do
      case "$1" in
        --all-agents) all_agents="true"; shift ;;
        --json) json_flag="true"; shift ;;
        *) shift ;;
      esac
    done
    python3 -c "
import json, glob, os
result = {}
for f in glob.glob('$OPENCLAW_DIR/agents/*/sessions/sessions.json'):
    with open(f) as fh:
        d = json.load(fh)
    result.update(d)
print(json.dumps(result, indent=2))
"
    ;;
  gateway)
    case "$subcmd" in
      restart)
        echo "[gateway] Stopping gateway..."
        sleep 0.1
        echo "[gateway] Starting gateway..."
        echo "[gateway] Gateway restarted successfully."
        # Write a restart marker for eval
        echo "$(date -Iseconds)" > "$OPENCLAW_DIR/.gateway_restart_marker"
        ;;
      status)
        echo "[gateway] Running on port 8080"
        ;;
    esac
    ;;
  status)
    python3 -c "
import json
with open('$CONFIG') as f:
    c = json.load(f)
bindings = c.get('bindings', [])
for b in bindings:
    peer = b.get('match', {}).get('peer', {})
    agent = b.get('agentId', '')
    chat_id = peer.get('id', '')
    kind = peer.get('kind', '')
    acct = b.get('match', {}).get('accountId', '')
    print(f'agent:{agent}:feishu:{kind}:{chat_id} (accountId={acct})')
"
    ;;
  *)
    echo "openclaw mock CLI: unknown command '$cmd'"
    exit 1
    ;;
esac
OPENCLAW_SCRIPT

chmod +x "$HOME_DIR/bin/openclaw"

# Ensure ~/bin is in PATH for all shells
export PATH="$HOME_DIR/bin:$PATH"
echo 'export PATH="$HOME/bin:$PATH"' >> "$HOME_DIR/.bashrc"
echo 'export PATH="$HOME/bin:$PATH"' >> "$HOME_DIR/.profile"

# Make the openclaw dir accessible
chmod -R 755 "$OPENCLAW_DIR"

echo "=== Setup complete ==="
echo "openclaw mock CLI installed at $HOME_DIR/bin/openclaw"
echo "DevOps Chat Group ID: $DEVOPS_CHAT_ID"
echo "Config: $OPENCLAW_DIR/openclaw.json"