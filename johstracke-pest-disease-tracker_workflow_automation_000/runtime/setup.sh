#!/bin/bash
set -e

# Ensure the pest_tracker.py is executable and accessible
chmod +x /usr/local/bin/pest_tracker.py

# Ensure workspace dirs exist
mkdir -p /root/.openclaw/workspace
mkdir -p /tmp

# Verify the tool works
python3 /usr/local/bin/pest_tracker.py list > /dev/null 2>&1 || true

echo "Setup complete. pest_tracker.py is ready."