#!/usr/bin/env bash
set -e

chmod +x /workspace/news-scraper/scripts/crawl.py

# Verify the mock data is present
python3 -c "
import sys, json
sys.path.insert(0, '/workspace/news-scraper')
from scripts.crawl import crawl_and_return_json
data = crawl_and_return_json(site='aibase', limit=20)
print(f'Mock crawl OK: {len(data)} articles loaded')
"

echo "Setup complete."