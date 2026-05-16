#!/bin/bash
set -e

# Ensure skill script is executable
chmod +x /skill/scripts/sentiment_scan.py

# Verify the skill script exists
if [ ! -f /skill/scripts/sentiment_scan.py ]; then
    echo "ERROR: sentiment_scan.py not found!" >&2
    exit 1
fi

# Verify workspace structure
if [ ! -f /workspace/portfolio_management/cross_market/portfolio_config.json ]; then
    echo "ERROR: portfolio_config.json not found!" >&2
    exit 1
fi

echo "Setup complete. Skill script available at /skill/scripts/sentiment_scan.py"
echo "Portfolio config available at /workspace/portfolio_management/cross_market/portfolio_config.json"