#!/bin/bash
set -e

# Create a mock 'openclaw' command so the agent can actually run it and we can capture what was called
cat > /usr/local/bin/openclaw << 'EOF'
#!/bin/bash
# Mock openclaw CLI - logs all invocations to a file
LOG_FILE="/workspace/logs/openclaw_invocations.log"
mkdir -p /workspace/logs
echo "$(date -Iseconds) openclaw $@" >> "$LOG_FILE"

# Parse and log cron add specifically
if [ "$1" = "cron" ] && [ "$2" = "add" ]; then
    echo "CRON_ADD: $@" >> "$LOG_FILE"
    echo "Cron job registered successfully."
fi
EOF
chmod +x /usr/local/bin/openclaw

# Ensure workspace directories exist
mkdir -p /workspace/logs/cron
mkdir -p /workspace/logs/heartbeat

# Set timezone to Asia/Shanghai for consistency
export TZ=Asia/Shanghai
echo "Asia/Shanghai" > /etc/timezone

echo "Setup complete. Mock openclaw available at $(which openclaw)"