#!/bin/bash
set -e

# Make all scripts executable
find /home/agent/workspace/scripts -name "*.sh" -exec chmod +x {} \;

# Install the agent's crontab from the file written by gen_inputs.py
CRONTAB_DIR="/var/spool/cron/crontabs"
mkdir -p "$CRONTAB_DIR"
CRONTAB_SRC="/home/agent/workspace/tmp/agent_crontab.txt"
if [ -f "$CRONTAB_SRC" ]; then
    cp "$CRONTAB_SRC" "$CRONTAB_DIR/agent"
    chown agent:crontab "$CRONTAB_DIR/agent" 2>/dev/null || chown agent:agent "$CRONTAB_DIR/agent" 2>/dev/null || true
    chmod 600 "$CRONTAB_DIR/agent"
fi
chown root:crontab "$CRONTAB_DIR" 2>/dev/null || chown root:root "$CRONTAB_DIR" 2>/dev/null || true
chmod 1730 "$CRONTAB_DIR" 2>/dev/null || chmod 700 "$CRONTAB_DIR" 2>/dev/null || true

# Install /etc/cron.d entry from workspace copy
CRON_D_SRC="/home/agent/workspace/config/jobs/fintech-rotate-keys"
if [ -f "$CRON_D_SRC" ]; then
    cp "$CRON_D_SRC" /etc/cron.d/fintech-rotate-keys
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