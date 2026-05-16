#!/bin/bash
set -e

# Make all Python scripts executable
chmod +x /workspace/main.py
chmod +x /workspace/subskills/config-optimization/optimize_from_aggressive.py
chmod +x /workspace/subskills/daily-recommendation/generate_daily_recommendation.py

# Ensure data directory exists and is writable
mkdir -p /workspace/data
chmod -R 755 /workspace/data

echo "[setup] Workspace ready."
ls -la /workspace/
echo "[setup] data/ contents:"
ls -la /workspace/data/