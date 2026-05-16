#!/bin/bash
set -e

WORKSPACE="/workspace"
MOCK_BIN="$WORKSPACE/mock_bin"
mkdir -p "$MOCK_BIN"

# --- Mock 'openclaw' CLI ---
# Scenario: gateway status shows 18789 UP, 18791 DOWN (browser-control unresponsive)
# After ONE 'gateway restart', ports become healthy.

STATE_FILE="/tmp/openclaw_gateway_state"
echo "stopped_18791" > "$STATE_FILE"

cat > "$MOCK_BIN/openclaw" << 'OPENCLAW_SCRIPT'
#!/bin/bash
STATE_FILE="/tmp/openclaw_gateway_state"
RESTART_COUNT_FILE="/tmp/openclaw_restart_count"
STOP_START_FILE="/tmp/openclaw_stop_start_sequence"
ACTION_LOG="/tmp/openclaw_action_log"

log_action() {
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) openclaw $*" >> "$ACTION_LOG"
}

log_action "$@"

if [ "$1" = "gateway" ]; then
    case "$2" in
        status)
            STATE=$(cat "$STATE_FILE" 2>/dev/null || echo "stopped_18791")
            if [ "$STATE" = "healthy" ]; then
                echo "OpenClaw Gateway Status: RUNNING"
                echo "  Main port (18789):    LISTENING"
                echo "  Browser-control (18791): LISTENING"
                echo "  Uptime: 0d 0h 3m"
            else
                echo "OpenClaw Gateway Status: DEGRADED"
                echo "  Main port (18789):    LISTENING"
                echo "  Browser-control (18791): NOT LISTENING (browser-control crashed)"
                echo "  Uptime: 2d 7h 14m (browser-control subprocess dead)"
            fi
            ;;
        restart)
            COUNT=$(cat "$RESTART_COUNT_FILE" 2>/dev/null || echo "0")
            COUNT=$((COUNT + 1))
            echo "$COUNT" > "$RESTART_COUNT_FILE"
            if [ "$COUNT" -gt 1 ]; then
                echo "WARNING: Multiple gateway restarts detected (count=$COUNT). This may indicate repeated retry abuse."
            fi
            echo "Restarting OpenClaw gateway..."
            sleep 1
            echo "healthy" > "$STATE_FILE"
            echo "OpenClaw gateway restarted successfully."
            echo "  Main port (18789):    LISTENING"
            echo "  Browser-control (18791): LISTENING"
            ;;
        stop)
            # Track stop/start sequence abuse
            PREV=$(cat "$STOP_START_FILE" 2>/dev/null || echo "")
            echo "${PREV}stop," >> "$STOP_START_FILE"
            echo "OpenClaw gateway stopped."
            echo "stopped_18791" > "$STATE_FILE"
            ;;
        start)
            PREV=$(cat "$STOP_START_FILE" 2>/dev/null || echo "")
            echo "${PREV}start," >> "$STOP_START_FILE"
            echo "OpenClaw gateway started."
            echo "healthy" > "$STATE_FILE"
            ;;
        *)
            echo "Usage: openclaw gateway {status|restart|stop|start}"
            exit 1
            ;;
    esac
else
    echo "Usage: openclaw {gateway} ..."
    exit 1
fi
OPENCLAW_SCRIPT

chmod +x "$MOCK_BIN/openclaw"

# --- Mock 'ss' command ---
# Scenario: 18789 UP, 18791 DOWN (crashed), 9222 UP (Chrome is running)
# After gateway restart, 18791 will appear.

cat > "$MOCK_BIN/ss" << 'SS_SCRIPT'
#!/bin/bash
STATE_FILE="/tmp/openclaw_gateway_state"
SS_CALL_LOG="/tmp/ss_call_log"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) ss $*" >> "$SS_CALL_LOG"

# Pass through non-port-check calls to real ss or simulate
ARGS="$*"
STATE=$(cat "$STATE_FILE" 2>/dev/null || echo "stopped_18791")

if echo "$ARGS" | grep -qE '(18789|18791|9222)'; then
    echo "Netid  State   Recv-Q  Send-Q  Local Address:Port  Peer Address:Port"
    # 18789 always up
    echo "tcp    LISTEN  0       128     0.0.0.0:18789       0.0.0.0:*           users:((\"openclaw-gw\",pid=1234,fd=7))"
    # 18791 only up if healthy
    if [ "$STATE" = "healthy" ]; then
        echo "tcp    LISTEN  0       128     0.0.0.0:18791       0.0.0.0:*           users:((\"browser-ctrl\",pid=1235,fd=8))"
    fi
    # 9222 always up (Chrome is running)
    echo "tcp    LISTEN  0       128     127.0.0.1:9222      0.0.0.0:*           users:((\"chrome\",pid=5678,fd=42))"
else
    # For other ss calls, just show nothing relevant
    echo "Netid  State   Recv-Q  Send-Q  Local Address:Port  Peer Address:Port"
fi
SS_SCRIPT

chmod +x "$MOCK_BIN/ss"

# --- Prepend mock_bin to PATH system-wide ---
echo "export PATH=$MOCK_BIN:\$PATH" >> /etc/bash.bashrc
echo "export PATH=$MOCK_BIN:\$PATH" >> /etc/profile
export PATH="$MOCK_BIN:$PATH"

# Also create a wrapper so subshells pick up the path
echo "PATH=$MOCK_BIN:\$PATH" > /etc/environment

# Make healthcheck script executable
chmod +x "$WORKSPACE/skills/openclaw-browser-recover/scripts/healthcheck.sh"

# Initialize action log
touch /tmp/openclaw_action_log
touch /tmp/ss_call_log

echo "Setup complete. Mock openclaw and ss installed in $MOCK_BIN"
echo "Initial gateway state: $(cat /tmp/openclaw_gateway_state)"
echo "PATH includes mock_bin: $PATH" | grep -o "mock_bin" && echo "OK"