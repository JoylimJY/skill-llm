#!/usr/bin/env bash
set -e

WORKSPACE="/workspace"

# Make all scripts executable
chmod +x "$WORKSPACE/scripts/price_tape.py"
chmod +x "$WORKSPACE/scripts/movers_yahoo.py"
chmod +x "$WORKSPACE/scripts/tmx_movers.py"

# Ensure reports directory exists
mkdir -p "$WORKSPACE/reports"

# Verify venv is intact
if [ ! -f "/root/.venvs/market-brief/bin/python" ]; then
    echo "ERROR: market-brief venv not found. Rebuilding..."
    python3 -m venv /root/.venvs/market-brief
    /root/.venvs/market-brief/bin/pip install -U pip -i https://pypi.tuna.tsinghua.edu.cn/simple
    /root/.venvs/market-brief/bin/pip install yfinance pandas numpy requests -i https://pypi.tuna.tsinghua.edu.cn/simple
fi

echo "Setup complete. Workspace ready at $WORKSPACE"
echo "Venv python: $(/root/.venvs/market-brief/bin/python --version)"