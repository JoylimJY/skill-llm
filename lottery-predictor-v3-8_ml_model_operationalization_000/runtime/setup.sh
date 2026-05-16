#!/bin/bash
set -e

chmod +x /workspace/lottery-predictor-v3-8/scripts/v3.8_ml_model.py
chmod +x /workspace/lottery-predictor-v3-8/scripts/backtest_v3.8.py

echo "Setup complete. Workspace ready."
echo "Note: LOTTERY_DB_PATH environment variable needs to be configured."