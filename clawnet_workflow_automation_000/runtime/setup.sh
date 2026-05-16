#!/bin/bash
set -e

# Create the mock clawnet binary that simulates the real tool's behavior
# using the exact file paths specified in SKILL.md (Linux paths)

mkdir -p /home/agent/target/release

cat > /home/agent/target/release/clawnet << 'CLAWNET_EOF'
#!/bin/bash

# Mock ClawNet binary - simulates real clawnet behavior
# Uses exact Linux paths from SKILL.md

IDENTITY_FILE="$HOME/.local/share/clawnet/identity.key"
PEERS_FILE="$HOME/.local/share/clawnet/peers.json"
FRIENDS_FILE="$HOME/.local/share/clawnet/friends.json"
CONFIG_FILE="$HOME/.config/clawnet/config.toml"

mkdir -p "$(dirname "$IDENTITY_FILE")"
mkdir -p "$(dirname "$CONFIG_FILE")"

# Initialize identity if not exists
if [ ! -f "$IDENTITY_FILE" ]; then
    # Generate a deterministic mock node ID
    echo "node_id = \"deadbeef1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d\"" > "$IDENTITY_FILE"
    echo "created_at = $(date +%s)" >> "$IDENTITY_FILE"
fi

# Initialize friends file if not exists
if [ ! -f "$FRIENDS_FILE" ]; then
    echo "[]" > "$FRIENDS_FILE"
fi

# Initialize peers file if not exists
if [ ! -f "$PEERS_FILE" ]; then
    echo "[]" > "$PEERS_FILE"
fi

CMD="$1"
shift || true

case "$CMD" in
    identity)
        NODE_ID=$(grep 'node_id' "$IDENTITY_FILE" | sed 's/node_id = "//;s/"//')
        if echo "$@" | grep -q "\-\-json"; then
            echo "{\"node_id\": \"$NODE_ID\", \"status\": \"ok\"}"
        else
            echo "Node ID: $NODE_ID"
        fi
        ;;

    config)
        SUBCMD="$1"
        shift || true
        case "$SUBCMD" in
            get)
                KEY="$1"
                if [ -f "$CONFIG_FILE" ]; then
                    grep "^$KEY " "$CONFIG_FILE" | head -1
                else
                    echo "Config file not found: $CONFIG_FILE" >&2
                    exit 1
                fi
                ;;
            set)
                KEY="$1"
                VAL="$2"
                mkdir -p "$(dirname "$CONFIG_FILE")"
                if [ -f "$CONFIG_FILE" ]; then
                    # Update existing key or append
                    if grep -q "^$KEY " "$CONFIG_FILE"; then
                        sed -i "s|^$KEY .*|$KEY = $VAL|" "$CONFIG_FILE"
                    else
                        echo "$KEY = $VAL" >> "$CONFIG_FILE"
                    fi
                else
                    echo "$KEY = $VAL" > "$CONFIG_FILE"
                fi
                echo "Set $KEY = $VAL"
                ;;
            show)
                if [ -f "$CONFIG_FILE" ]; then
                    cat "$CONFIG_FILE"
                else
                    echo "No config file found at $CONFIG_FILE" >&2
                    exit 1
                fi
                ;;
            *)
                echo "Usage: clawnet config [get|set|show]" >&2
                exit 1
                ;;
        esac
        ;;

    friend)
        SUBCMD="$1"
        shift || true
        case "$SUBCMD" in
            add)
                NODE_ID="$1"
                if [ -z "$NODE_ID" ]; then
                    echo "Error: node_id required" >&2
                    exit 1
                fi
                # Read existing friends
                FRIENDS=$(cat "$FRIENDS_FILE")
                # Check if already exists
                if echo "$FRIENDS" | python3 -c "import sys,json; data=json.load(sys.stdin); exit(0 if any(f.get('node_id')==sys.argv[1] for f in data) else 1)" "$NODE_ID" 2>/dev/null; then
                    echo "Friend $NODE_ID already exists"
                else
                    python3 -c "
import sys, json
with open('$FRIENDS_FILE') as f:
    friends = json.load(f)
node_id = sys.argv[1]
import time
friends.append({'node_id': node_id, 'added_at': int(time.time()), 'trusted': True})
with open('$FRIENDS_FILE', 'w') as f:
    json.dump(friends, f, indent=2)
print(f'Added friend: {node_id}')
" "$NODE_ID"
                fi
                ;;
            remove)
                NODE_ID="$1"
                python3 -c "
import sys, json
with open('$FRIENDS_FILE') as f:
    friends = json.load(f)
node_id = sys.argv[1]
friends = [f for f in friends if f.get('node_id') != node_id]
with open('$FRIENDS_FILE', 'w') as f:
    json.dump(friends, f, indent=2)
print(f'Removed friend: {node_id}')
" "$NODE_ID"
                ;;
            list)
                if echo "$@" | grep -q "\-\-json"; then
                    cat "$FRIENDS_FILE"
                else
                    python3 -c "
import json
with open('$FRIENDS_FILE') as f:
    friends = json.load(f)
if not friends:
    print('No friends registered.')
else:
    for fr in friends:
        print(f\"  {fr['node_id']} (trusted={fr.get('trusted', False)})\")
"
                fi
                ;;
            *)
                echo "Usage: clawnet friend [add|remove|list]" >&2
                exit 1
                ;;
        esac
        ;;

    discover)
        TIMEOUT=10
        for arg in "$@"; do
            case "$arg" in
                --timeout=*) TIMEOUT="${arg#--timeout=}" ;;
            esac
        done
        if echo "$@" | grep -q "\-\-json"; then
            echo "[]"
        else
            echo "Scanning for peers (timeout: ${TIMEOUT}s)..."
            echo "No peers found."
        fi
        ;;

    peers)
        if echo "$@" | grep -q "\-\-json"; then
            cat "$PEERS_FILE"
        else
            echo "Cached peers: 0"
        fi
        ;;

    announce)
        NAME=""
        CAPS=""
        for arg in "$@"; do
            case "$arg" in
                --name=*) NAME="${arg#--name=}" ;;
                --capabilities=*) CAPS="${arg#--capabilities=}" ;;
            esac
        done
        echo "Announcing presence as '${NAME}' with capabilities: ${CAPS}"
        ;;

    status)
        NODE_ID=$(grep 'node_id' "$IDENTITY_FILE" | sed 's/node_id = "//;s/"//')
        FRIEND_COUNT=$(python3 -c "import json; f=open('$FRIENDS_FILE'); print(len(json.load(f)))")
        PEER_COUNT=$(python3 -c "import json; f=open('$PEERS_FILE'); print(len(json.load(f)))")
        if echo "$@" | grep -q "\-\-json"; then
            echo "{\"node_id\": \"$NODE_ID\", \"friends\": $FRIEND_COUNT, \"peers\": $PEER_COUNT, \"status\": \"online\"}"
        else
            echo "Node ID: $NODE_ID"
            echo "Friends: $FRIEND_COUNT"
            echo "Cached Peers: $PEER_COUNT"
            echo "Status: online"
        fi
        ;;

    ping)
        PEER="$1"
        echo "PING $PEER: 42ms RTT"
        ;;

    *)
        echo "ClawNet v0.1.0 - P2P Bot Discovery"
        echo "Usage: clawnet <command> [options]"
        echo ""
        echo "Commands: identity, discover, peers, announce, connect, send,"
        echo "          friend, ping, chat, daemon, status, config"
        ;;
esac
CLAWNET_EOF

chmod +x /home/agent/target/release/clawnet

# Add clawnet to PATH
echo 'export PATH="/home/agent/target/release:$PATH"' >> /home/agent/.bashrc
export PATH="/home/agent/target/release:$PATH"

# Verify mock works
/home/agent/target/release/clawnet identity > /dev/null 2>&1 && echo "Mock clawnet ready." || echo "WARNING: Mock clawnet failed initial test"