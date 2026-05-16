#!/bin/bash
set -e

# Ensure workspace directory exists
mkdir -p /workspace/output

# Verify mock akshare is in place
python3 -c "import akshare as ak; df = ak.stock_board_industry_cons_em(symbol='半导体'); print(f'Mock akshare OK: {len(df)} stocks found')"

# Make scripts executable
chmod +x /workspace/scripts/backtest/legacy_fetch.py 2>/dev/null || true
chmod +x /workspace/scripts/utils/sector_old.py 2>/dev/null || true

echo "Setup complete. Mock AkShare is active."
echo "Agent workspace is ready at /workspace"