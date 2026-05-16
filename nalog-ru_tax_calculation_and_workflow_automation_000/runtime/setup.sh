#!/bin/bash
set -e

# Ensure openclaw directory exists with correct permissions
mkdir -p /home/node/.openclaw/workspace
chmod -R 777 /home/node/.openclaw/

# Verify the counter file is in place
if [ ! -f /home/node/.openclaw/workspace/ru-pack-counter.txt ]; then
    echo "2" > /home/node/.openclaw/workspace/ru-pack-counter.txt
fi

echo "Setup complete. Counter value: $(cat /home/node/.openclaw/workspace/ru-pack-counter.txt)"