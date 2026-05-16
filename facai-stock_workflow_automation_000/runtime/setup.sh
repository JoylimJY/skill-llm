#!/usr/bin/env bash
set -e

cd /workspace
chmod +x scripts/utils/calc_macd.py scripts/analysis/backtest.py 2>/dev/null || true

echo "[setup] Workspace ready."