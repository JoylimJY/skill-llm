#!/usr/bin/env bash
set -euo pipefail

echo "=== Setup: ensuring scripts are executable ==="
chmod +x /workspace/scripts/run_query.sh
chmod +x /workspace/scripts/test_markets.sh

echo "=== Setup: verifying tvscreener installation ==="
python3 -c "from tvscreener import StockScreener, Market; print('tvscreener OK')"

echo "=== Setup: workspace listing ==="
find /workspace -type f | sort

echo "=== Setup complete ==="