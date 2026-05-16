#!/bin/bash
set -e

# Make all scripts executable
chmod +x /workspace/scripts/baidu_search.py
chmod +x /workspace/scripts/fetch_url.py
chmod +x /workspace/scripts/search_and_fetch.py

# Ensure Python path is set correctly
export PYTHONPATH=/workspace:$PYTHONPATH

# Verify the mock baidusearch package is importable
python3 -c "
import sys
sys.path.insert(0, '/workspace')
from baidusearch.baidusearch import search, fetch_page
results = search('新能源汽车市场份额', num_results=3)
assert len(results) == 3, f'Expected 3 results, got {len(results)}'
assert 'title' in results[0], 'Missing title key'
assert 'abstract' in results[0], 'Missing abstract key'
assert 'url' in results[0], 'Missing url key'
assert 'rank' in results[0], 'Missing rank key'
assert results[0]['rank'] == 1, f'First result rank should be 1, got {results[0][\"rank\"]}'
print('Mock baidusearch package verified OK')
"

# Verify scripts work
python3 /workspace/scripts/baidu_search.py "新能源汽车市场份额" --num 3 > /dev/null
echo "baidu_search.py script verified OK"

python3 /workspace/scripts/fetch_url.py "http://mock.local/article/nev-market-2024" > /dev/null
echo "fetch_url.py script verified OK"

echo "Setup complete. All tools verified."