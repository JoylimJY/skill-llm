#!/bin/bash
set -e

chmod +x /workspace/main.py
chmod +x /workspace/subskills/config-optimization/optimize_from_aggressive.py
chmod +x /workspace/subskills/daily-recommendation/generate_daily_recommendation.py

echo "[setup] Workspace ready. main.py is executable."
echo "[setup] Current decision_log.jsonl entries:"
wc -l /workspace/data/decision_log.jsonl