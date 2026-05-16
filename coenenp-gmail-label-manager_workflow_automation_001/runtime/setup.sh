#!/bin/bash
set -e

# Ensure gog is on PATH
ln -sf /workspace/gog /usr/local/bin/gog
chmod +x /workspace/gog
chmod +x /workspace/script.sh

# Verify gog is executable
gog gmail messages search "is:unread" --max 1 --json > /dev/null 2>&1 && echo "[setup] gog mock CLI verified OK" || echo "[setup] Warning: gog test failed"

# Create logs directory
mkdir -p /workspace/logs

echo "[setup] Workspace initialized successfully."