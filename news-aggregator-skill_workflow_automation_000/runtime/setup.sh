#!/bin/bash
set -e

echo "[setup] Making scripts executable..."
chmod +x /workspace/scripts/fetch_news.py

echo "[setup] Verifying mock script runs..."
python3 /workspace/scripts/fetch_news.py --source github --limit 3 --deep > /dev/null && echo "[setup] Mock script OK"

echo "[setup] Creating reports directory if missing..."
mkdir -p /workspace/reports

echo "[setup] Environment ready."