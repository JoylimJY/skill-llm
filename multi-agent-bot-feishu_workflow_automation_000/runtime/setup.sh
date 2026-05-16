#!/bin/bash
set -e

# Ensure openclaw CLI is executable
chmod +x /usr/local/bin/openclaw

# Verify the config file is in place
if [ ! -f "$HOME/.openclaw/openclaw.json" ]; then
    echo "ERROR: openclaw.json not found!"
    exit 1
fi

echo "Setup complete. OpenClaw sandbox is ready."
echo "Config file contents:"
cat "$HOME/.openclaw/openclaw.json"