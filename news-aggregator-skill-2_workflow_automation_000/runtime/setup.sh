#!/bin/bash
set -e

# Make fetch_news.py executable
chmod +x /workspace/scripts/fetch_news.py

# Verify mock data is readable
python3 -c "import json; data=json.load(open('/workspace/scripts/_mock_news_data.json')); print(f'Mock data loaded: {len(data)} items')"

# Ensure reports directory exists and is writable
mkdir -p /workspace/reports
chmod 777 /workspace/reports

# Quick sanity check: does the mock script run?
cd /workspace
python3 scripts/fetch_news.py --source all --limit 15 --deep > /tmp/sanity_check.json 2>&1
ITEM_COUNT=$(python3 -c "import json; print(len(json.load(open('/tmp/sanity_check.json'))))")
echo "Sanity check: fetch_news.py returned ${ITEM_COUNT} items for --source all --limit 15 --deep"

echo "Setup complete. Workspace ready for agent."