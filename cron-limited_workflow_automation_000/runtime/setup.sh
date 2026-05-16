#!/bin/bash
set -e

# Ensure openclaw mock is executable
chmod +x /usr/local/bin/openclaw

# Create openclaw config directories
mkdir -p ~/.openclaw/cron-limited
mkdir -p ~/.openclaw

# Initialize empty call log
touch ~/.openclaw/call_log.jsonl

# Set timezone to Shanghai for the container
export TZ=Asia/Shanghai
ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime 2>/dev/null || true
echo "Asia/Shanghai" > /etc/timezone 2>/dev/null || true

echo "Setup complete. Mock openclaw CLI is ready."
echo "Call log will be written to: ~/.openclaw/call_log.jsonl"