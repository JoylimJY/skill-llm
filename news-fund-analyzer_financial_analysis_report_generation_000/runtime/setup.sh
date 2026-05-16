#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace/

echo "Verifying input files..."
for f in \
    "/workspace/data/fund/fund_info.json" \
    "/workspace/data/market/market_data.json" \
    "/workspace/data/news/news_articles.json" \
    "/workspace/data/fund/user_profile.json"; do
    if [ -f "$f" ]; then
        echo "  [OK] $f"
    else
        echo "  [MISSING] $f"
        exit 1
    fi
done

echo "Setup complete. Workspace ready for agent."