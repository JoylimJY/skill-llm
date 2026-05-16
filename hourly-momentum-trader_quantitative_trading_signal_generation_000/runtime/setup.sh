#!/usr/bin/env bash
set -e

# Make the workspace fully accessible
chmod -R 755 /workspace

echo "[setup] Workspace initialized. Contents of data/raw/candles:"
ls /workspace/data/raw/candles/

echo "[setup] Polymarket odds:"
cat /workspace/data/raw/polymarket_odds.json

echo "[setup] TASK.txt:"
cat /workspace/TASK.txt

echo "[setup] Done."