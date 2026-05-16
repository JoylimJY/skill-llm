FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    bash \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    jsonschema \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

# Create openclaw mock CLI
RUN mkdir -p /usr/local/bin

# Write the mock openclaw CLI as a shell script
RUN cat > /usr/local/bin/openclaw << 'CLIEOF'
#!/bin/bash
# Mock openclaw CLI for testing

AGENTS_FILE="/root/.openclaw/agents.json"
LOG_FILE="/root/.openclaw/mock_cli.log"
mkdir -p /root/.openclaw

echo "[openclaw mock] called with args: $@" >> "$LOG_FILE"

if [ "$1" = "agents" ] && [ "$2" = "add" ]; then
    AGENT_ID="$3"
    shift 3
    WORKSPACE=""
    MODEL=""
    NON_INTERACTIVE=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --workspace) WORKSPACE="$2"; shift 2;;
            --model) MODEL="$2"; shift 2;;
            --non-interactive) NON_INTERACTIVE=true; shift;;
            *) shift;;
        esac
    done
    
    if [ "$NON_INTERACTIVE" != "true" ]; then
        echo "ERROR: --non-interactive flag is required for automated agent creation." >&2
        exit 2
    fi
    
    if [ -z "$AGENT_ID" ]; then
        echo "ERROR: agent_id is required." >&2
        exit 1
    fi
    
    # Load or initialize agents file
    if [ ! -f "$AGENTS_FILE" ]; then
        echo '{"agents":[]}' > "$AGENTS_FILE"
    fi
    
    # Add agent entry
    ENTRY="{\"id\":\"$AGENT_ID\",\"workspace\":\"$WORKSPACE\""
    if [ -n "$MODEL" ]; then
        ENTRY="$ENTRY,\"model\":\"$MODEL\""
    fi
    ENTRY="$ENTRY}"
    
    python3 -c "
import json, sys
with open('$AGENTS_FILE') as f:
    data = json.load(f)
entry = json.loads('$ENTRY')
data['agents'] = [a for a in data['agents'] if a['id'] != entry['id']]
data['agents'].append(entry)
with open('$AGENTS_FILE', 'w') as f:
    json.dump(data, f, indent=2)
print(f'Agent {entry[\"id\"]} created.')
"
    exit 0
fi

if [ "$1" = "gateway" ] && [ "$2" = "restart" ]; then
    echo "Gateway restarted successfully." | tee -a "$LOG_FILE"
    echo "gateway_restarted=true" >> /root/.openclaw/gateway_state
    exit 0
fi

if [ "$1" = "agents" ] && [ "$2" = "list" ]; then
    BINDINGS=false
    if [ "$3" = "--bindings" ]; then
        BINDINGS=true
    fi
    
    CONFIG="/root/.openclaw/openclaw.json"
    if [ ! -f "$CONFIG" ]; then
        echo "No config found." >&2
        exit 1
    fi
    
    python3 -c "
import json
with open('$CONFIG') as f:
    config = json.load(f)

agents_file = '$AGENTS_FILE'
try:
    with open(agents_file) as f:
        agents_data = json.load(f)
    agents = agents_data.get('agents', [])
except:
    agents = []

bindings = config.get('bindings', [])
print('AGENTS:')
for a in agents:
    print(f'  - {a[\"id\"]} (workspace: {a.get(\"workspace\",\"N/A\")})')

if $BINDINGS:
    print('BINDINGS:')
    for b in bindings:
        print(f'  - agent={b.get(\"agent_id\",\"?\")} channel={b.get(\"channel\",\"?\")} routing_mode={b.get(\"routing_mode\",\"?\")} peer_id={b.get(\"peer_id\",\"\")} account_id={b.get(\"account_id\",\"\")}')
"
    exit 0
fi

if [ "$1" = "logs" ] && [ "$2" = "--follow" ]; then
    echo 'Received message from peer: { kind: "group", id: "oc_abc123followtest" }'
    exit 0
fi

echo "Unknown command: $@" >&2
exit 1
CLIEOF

RUN chmod +x /usr/local/bin/openclaw

WORKDIR /workspace