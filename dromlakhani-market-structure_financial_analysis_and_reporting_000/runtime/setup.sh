#!/usr/bin/env bash
set -e

# Ensure workspace permissions
chmod -R 755 /workspace

echo "[setup] Workspace ready."
echo "[setup] Primary data file: /workspace/data/raw/xauusd/xauusd_4h_march2024.csv"
echo "[setup] Task: Produce market_analysis_XAUUSD.md in the workspace."