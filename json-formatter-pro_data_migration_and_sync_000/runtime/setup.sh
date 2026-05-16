#!/bin/bash
set -e

# Ensure the formatter script is executable
chmod +x /root/.openclaw/skills/json-formatter-pro/json_formatter.py

# Verify the script exists
if [ ! -f /root/.openclaw/skills/json-formatter-pro/json_formatter.py ]; then
    echo "ERROR: json_formatter.py not found!" >&2
    exit 1
fi

echo "Setup complete. Formatter skill ready at /root/.openclaw/skills/json-formatter-pro/json_formatter.py"