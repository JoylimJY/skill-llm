#!/bin/bash
set -e

chmod +x /workspace/scripts/fetch_markets.sh 2>/dev/null || true

echo "Workspace ready. Market opportunity batch available at /workspace/market_data/raw/opportunity_batch.json"
echo "Bankroll config at /workspace/strategy/configs/bankroll.json"