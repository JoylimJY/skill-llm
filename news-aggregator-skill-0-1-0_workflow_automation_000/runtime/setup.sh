#!/bin/bash
set -e

echo "=== Setting up news-aggregator sandbox ==="

# Ensure fetch_news.py is executable
chmod +x /workspace/scripts/fetch_news.py

# Initialize the fetch call log (fresh start for eval)
mkdir -p /workspace/logs
echo "" > /workspace/logs/fetch_calls.log

# Ensure reports directory exists
mkdir -p /workspace/reports

# Verify mock script is functional
echo "=== Verifying mock fetch_news.py ==="
cd /workspace
python3 scripts/fetch_news.py --source hackernews --limit 5 --keyword "AI,LLM,GPT,Claude,Generative,Machine Learning,RAG,Agent" --deep | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Mock OK: {len(d)} items returned')"

python3 scripts/fetch_news.py --source github --limit 10 --deep | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'GitHub mock OK: {len(d)} items returned')"

echo "=== Setup complete. Agent may now begin. ==="