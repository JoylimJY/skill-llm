#!/usr/bin/env bash
set -e

chmod +x /workspace/scripts/sentiment_analyzer.py
chmod +x /workspace/scripts/sector_flow.py
chmod +x /workspace/scripts/cross_market.py

# Quick smoke test — make sure the scripts actually run
python3 /workspace/scripts/sentiment_analyzer.py --date 2026-03-15 > /dev/null
python3 /workspace/scripts/sector_flow.py --date 2026-03-15 > /dev/null
python3 /workspace/scripts/cross_market.py --date 2026-03-15 > /dev/null

echo "Setup complete: all mock scripts verified."