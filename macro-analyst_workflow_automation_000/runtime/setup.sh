#!/usr/bin/env bash
set -e

# Ensure all scripts are executable
chmod +x /workspace/skills/akshare-finance/scripts/macro_data.py
chmod +x /workspace/skills/akshare-finance/scripts/earnings.py
chmod +x /workspace/workspace-trading/skills/trading-quant/scripts/quant.py

# Verify python3.12 is available (it's the container default python3.12)
python3.12 --version

echo "Setup complete."