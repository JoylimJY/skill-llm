#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying data files..."
for f in \
    "/workspace/market_data/candles/btc_1d.json" \
    "/workspace/market_data/candles/btc_1h.json" \
    "/workspace/market_data/candles/btc_4h.json" \
    "/workspace/market_data/candles/btc_15m.json" \
    "/workspace/market_data/candles/btc_5m.json" \
    "/workspace/market_data/candles/btc_1m.json" \
    "/workspace/market_data/sentiment/funding_and_ratio.json" \
    "/workspace/market_data/liquidations/btc_liq_clusters.json"; do
    if [ -f "$f" ]; then
        echo "  [OK] $f"
    else
        echo "  [MISSING] $f"
        exit 1
    fi
done

echo "Setup complete. Agent may begin analysis."