#!/bin/bash
set -e

echo "=== Setting up sandbox environment ==="

# Ensure ncm-cli mock is executable
chmod +x /usr/local/bin/ncm-cli

# Ensure config directories exist
mkdir -p /root/.config/ncm

# Ensure cron is available and initialized
service cron start 2>/dev/null || true
# Initialize empty crontab if none exists
crontab -l 2>/dev/null | crontab - 2>/dev/null || echo "" | crontab -

# Verify mock CLI works
echo "--- Testing mock ncm-cli ---"
ncm-cli playlist liked 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Liked songs: {len(d[\"songs\"])} total')" || echo "WARNING: ncm-cli test failed"
ncm-cli search --keyword "周杰伦" --type playlist --limit 4 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Search results: {len(d[\"result\"][\"playlists\"])} playlists')" || echo "WARNING: search test failed"

echo "=== Setup complete ==="