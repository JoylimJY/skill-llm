#!/usr/bin/env bash
set -e

# Ensure workspace scripts are readable
chmod -R 755 /workspace/scripts/

# Ensure the openclaw home directory is accessible
chmod -R 755 ~/.openclaw/ 2>/dev/null || true

# Create a mock 'openclaw' CLI that does nothing (simulates gateway restart)
cat > /usr/local/bin/openclaw << 'EOF'
#!/usr/bin/env bash
# Mock OpenClaw CLI - records invocations for eval
LOGFILE="/tmp/openclaw_invocations.log"
echo "$(date -Iseconds) openclaw $@" >> "$LOGFILE"
if [[ "$1" == "gateway" && "$2" == "restart" ]]; then
    echo "[Gateway] Restarting OpenClaw gateway..."
    echo "[Gateway] Loading plugins from ~/.openclaw/workspace/.openclaw/extensions/"
    echo "[Gateway] Gateway restarted successfully."
fi
exit 0
EOF
chmod +x /usr/local/bin/openclaw

echo "Setup complete. Mock openclaw CLI installed at /usr/local/bin/openclaw"