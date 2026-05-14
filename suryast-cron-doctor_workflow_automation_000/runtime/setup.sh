#!/bin/bash
set -e

# Make all scripts executable
find /home/agent/workspace/scripts -name "*.sh" -exec chmod +x {} \;

# Ensure crontab directory ownership is correct so `crontab -l` works
CRONTAB_DIR="/var/spool/cron/crontabs"
if [ -d "$CRONTAB_DIR" ]; then
    chown -R agent:agent "$CRONTAB_DIR" 2>/dev/null || true
    chmod 700 "$CRONTAB_DIR" 2>/dev/null || true
    if [ -f "$CRONTAB_DIR/agent" ]; then
        chmod 600 "$CRONTAB_DIR/agent" 2>/dev/null || true
    fi
fi

# Create /etc/cron.d entry (already written by gen_inputs, ensure it's readable)
if [ -f /etc/cron.d/fintech-rotate-keys ]; then
    chmod 644 /etc/cron.d/fintech-rotate-keys
fi

# Ensure /var/log/syslog has correct permissions so agent can read it
if [ -f /var/log/syslog ]; then
    chmod 644 /var/log/syslog 2>/dev/null || true
fi

# Ensure reports directory exists and is writable
mkdir -p /home/agent/workspace/reports
chown agent:agent /home/agent/workspace/reports

# Ensure all log files in /tmp are readable
chmod 644 /tmp/sync_trades.log /tmp/db_backup.log /tmp/audit_logins.log \
          /tmp/rotate_keys.log /tmp/daily_pnl.log /tmp/market_feed.log 2>/dev/null || true

echo "Setup complete."