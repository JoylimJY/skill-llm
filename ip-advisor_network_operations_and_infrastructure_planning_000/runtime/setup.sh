#!/bin/bash
set -e

# Install ip-advisor tool
cd /workspace

# Install the ip-advisor npm package globally
npm install -g ip-advisor 2>/dev/null || true

# Check if ip-advisor installs as a package providing script.sh
# The SKILL.md says scripts already exist; let's locate or bootstrap the scripts dir.
# Since the skill says "scripts/script.sh", set up the scripts dir in /workspace
mkdir -p /workspace/scripts

# Try to find the installed ip-advisor binary and its scripts
IP_ADV_BIN=$(which ip-advisor 2>/dev/null || true)
IP_ADV_NODE=$(npm root -g 2>/dev/null)/ip-advisor

if [ -d "$IP_ADV_NODE" ]; then
    echo "Found ip-advisor node module at $IP_ADV_NODE"
    # Check for script.sh inside the package
    if [ -f "$IP_ADV_NODE/scripts/script.sh" ]; then
        cp "$IP_ADV_NODE/scripts/script.sh" /workspace/scripts/script.sh
        chmod +x /workspace/scripts/script.sh
        echo "Copied script.sh from npm package"
    fi
fi

# If we have it in the scripts dir already or via another mechanism, chmod it
if [ -f "/workspace/scripts/script.sh" ]; then
    chmod +x /workspace/scripts/script.sh
    echo "script.sh is ready at /workspace/scripts/script.sh"
else
    # Build a fully functional mock script.sh that implements ip-advisor commands
    # using pure bash/python as a stand-in so the sandbox works deterministically
    cat > /workspace/scripts/script.sh << 'SCRIPT_EOF'
#!/bin/bash

# ip-advisor v3.0.0 - mock implementation for sandbox

DATA_DIR="$HOME/.local/share/ip-advisor"
mkdir -p "$DATA_DIR"

# Helper: validate an IP
validate_ip() {
    local ip="$1"
    if [[ "$ip" =~ ^([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})\.([0-9]{1,3})$ ]]; then
        local o1="${BASH_REMATCH[1]}" o2="${BASH_REMATCH[2]}" o3="${BASH_REMATCH[3]}" o4="${BASH_REMATCH[4]}"
        if [ "$o1" -le 255 ] && [ "$o2" -le 255 ] && [ "$o3" -le 255 ] && [ "$o4" -le 255 ]; then
            echo "valid"
            return 0
        fi
    fi
    echo "invalid"
    return 1
}

# Helper: IP to integer
ip2int() {
    local ip="$1"
    local o1 o2 o3 o4
    IFS='.' read -r o1 o2 o3 o4 <<< "$ip"
    echo $(( (o1 << 24) + (o2 << 16) + (o3 << 8) + o4 ))
}

# Helper: integer to IP
int2ip() {
    local n="$1"
    echo "$(( (n >> 24) & 255 )).$(( (n >> 16) & 255 )).$(( (n >> 8) & 255 )).$(( n & 255 ))"
}

CMD="$1"

case "$CMD" in
    info)
        IP="$2"
        RESULT=$(validate_ip "$IP")
        if [ "$RESULT" = "valid" ]; then
            IFS='.' read -r o1 o2 o3 o4 <<< "$IP"
            # Determine class
            if [ "$o1" -le 127 ]; then CLASS="A"
            elif [ "$o1" -le 191 ]; then CLASS="B"
            elif [ "$o1" -le 223 ]; then CLASS="C"
            else CLASS="D/E"
            fi
            # Private check
            PRIVATE="false"
            if [ "$o1" -eq 10 ]; then PRIVATE="true"; fi
            if [ "$o1" -eq 172 ] && [ "$o2" -ge 16 ] && [ "$o2" -le 31 ]; then PRIVATE="true"; fi
            if [ "$o1" -eq 192 ] && [ "$o2" -eq 168 ]; then PRIVATE="true"; fi
            echo "{\"ip\": \"$IP\", \"class\": \"$CLASS\", \"private\": $PRIVATE}"
        else
            echo "{\"error\": \"Invalid IP address: $IP\"}"
        fi
        ;;
    subnet)
        CIDR="$2"
        if [[ "$CIDR" =~ ^([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})/([0-9]+)$ ]]; then
            BASE_IP="${BASH_REMATCH[1]}"
            PREFIX="${BASH_REMATCH[2]}"
            if [ "$PREFIX" -lt 0 ] || [ "$PREFIX" -gt 32 ]; then
                echo "{\"error\": \"Invalid prefix length\"}"
                exit 1
            fi
            # Mask
            if [ "$PREFIX" -eq 0 ]; then
                MASK=0
            else
                MASK=$(( 0xFFFFFFFF << (32 - PREFIX) & 0xFFFFFFFF ))
            fi
            MASK_IP="$(( (MASK >> 24) & 255 )).$(( (MASK >> 16) & 255 )).$(( (MASK >> 8) & 255 )).$(( MASK & 255 ))"
            BASE_INT=$(ip2int "$BASE_IP")
            NETWORK_INT=$(( BASE_INT & MASK ))
            NETWORK_IP=$(int2ip $NETWORK_INT)
            BROADCAST_INT=$(( NETWORK_INT | (~MASK & 0xFFFFFFFF) ))
            BROADCAST_IP=$(int2ip $BROADCAST_INT)
            TOTAL_HOSTS=$(( 1 << (32 - PREFIX) ))
            USABLE=$(( TOTAL_HOSTS - 2 ))
            if [ "$USABLE" -lt 0 ]; then USABLE=0; fi
            FIRST_INT=$(( NETWORK_INT + 1 ))
            LAST_INT=$(( BROADCAST_INT - 1 ))
            FIRST_IP=$(int2ip $FIRST_INT)
            LAST_IP=$(int2ip $LAST_INT)
            echo "{\"cidr\": \"$CIDR\", \"network\": \"$NETWORK_IP\", \"broadcast\": \"$BROADCAST_IP\", \"netmask\": \"$MASK_IP\", \"prefix\": $PREFIX, \"total_hosts\": $TOTAL_HOSTS, \"usable_hosts\": $USABLE, \"first_host\": \"$FIRST_IP\", \"last_host\": \"$LAST_IP\"}"
        else
            echo "{\"error\": \"Invalid CIDR notation: $CIDR\"}"
        fi
        ;;
    validate)
        IP="$2"
        RESULT=$(validate_ip "$IP")
        if [ "$RESULT" = "valid" ]; then
            echo "{\"ip\": \"$IP\", \"valid\": true}"
        else
            echo "{\"ip\": \"$IP\", \"valid\": false}"
        fi
        ;;
    local)
        # Get local IPs
        ADDRS=$(ip -4 addr show 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -5 | tr '\n' ',' | sed 's/,$//')
        echo "{\"local_addresses\": [\"${ADDRS//,/\",\"}\"]}"
        ;;
    public)
        # Mock public IP
        echo "{\"public_ip\": \"203.0.113.42\", \"note\": \"simulated\"}"
        ;;
    range)
        START="$2"
        END="$3"
        if [ -z "$START" ] || [ -z "$END" ]; then
            echo "{\"error\": \"Usage: range <start> <end>\"}"
            exit 1
        fi
        START_V=$(validate_ip "$START")
        END_V=$(validate_ip "$END")
        if [ "$START_V" != "valid" ] || [ "$END_V" != "valid" ]; then
            echo "{\"error\": \"Invalid IP in range\"}"
            exit 1
        fi
        START_INT=$(ip2int "$START")
        END_INT=$(ip2int "$END")
        if [ "$START_INT" -gt "$END_INT" ]; then
            echo "{\"error\": \"Start IP must be <= End IP\"}"
            exit 1
        fi
        COUNT=$(( END_INT - START_INT + 1 ))
        IPS="["
        for ((i=0; i<COUNT; i++)); do
            IP_STR=$(int2ip $(( START_INT + i )))
            if [ $i -eq 0 ]; then
                IPS="$IPS\"$IP_STR\""
            else
                IPS="$IPS,\"$IP_STR\""
            fi
        done
        IPS="$IPS]"
        echo "{\"start\": \"$START\", \"end\": \"$END\", \"count\": $COUNT, \"ips\": $IPS}"
        ;;
    *)
        echo "{\"error\": \"Unknown command: $CMD\"}"
        exit 1
        ;;
esac
SCRIPT_EOF
    chmod +x /workspace/scripts/script.sh
    echo "Created mock script.sh implementation"
fi

echo "ip-advisor setup complete."
echo "Test: $(bash /workspace/scripts/script.sh validate 10.0.1.5)"