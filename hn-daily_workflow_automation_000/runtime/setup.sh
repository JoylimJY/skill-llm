#!/bin/bash
set -e

# Ensure the fetch script is executable
chmod +x /workspace/scripts/fetch_hn.py

# Verify the cache was created by gen_inputs_script
CACHE_FILE="$HOME/.cache/hn-daily/hn_cache.json"
if [ -f "$CACHE_FILE" ]; then
    echo "[setup] Cache file present: $CACHE_FILE"
    STORY_COUNT=$(python3 -c "import json; d=json.load(open('$CACHE_FILE')); print(len(d['stories']))")
    echo "[setup] Cache contains $STORY_COUNT stories"
else
    echo "[setup] WARNING: Cache file not found at $CACHE_FILE"
fi

# Confirm scripts directory structure
echo "[setup] scripts/ contents:"
ls -la /workspace/scripts/

echo "[setup] Workspace ready."