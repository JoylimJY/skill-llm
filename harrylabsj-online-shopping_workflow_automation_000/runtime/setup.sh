#!/bin/bash
set -e

# Make the main script executable
chmod +x /workspace/online-shopping.py

# Verify data files are in place
echo "[setup] Checking data files..."
for f in /workspace/data/platforms.json /workspace/data/categories.json /workspace/data/regions.json; do
    if [ -f "$f" ]; then
        echo "[setup] OK: $f"
    else
        echo "[setup] MISSING: $f"
        exit 1
    fi
done

# Verify the main script works
echo "[setup] Testing online-shopping.py..."
cd /workspace && python3 online-shopping.py categories > /dev/null 2>&1 && echo "[setup] Script OK" || echo "[setup] Script test failed"

echo "[setup] Workspace ready."