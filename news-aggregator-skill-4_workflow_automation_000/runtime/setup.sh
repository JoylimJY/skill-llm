#!/bin/bash
set -e

echo "=== Setting up news-aggregator sandbox ==="

# Ensure scripts directory is executable
chmod +x /workspace/scripts/fetch_news.py

# Ensure reports directory exists and is writable
mkdir -p /workspace/reports
chmod 755 /workspace/reports

# Smoke-test the mock script
echo "--- Smoke test: github source ---"
python3 /workspace/scripts/fetch_news.py --source github --limit 5 --deep | python3 -c "import json,sys; data=json.load(sys.stdin); print(f'GitHub items returned: {len(data)}')"

echo "--- Smoke test: hackernews with keyword ---"
python3 /workspace/scripts/fetch_news.py --source hackernews --limit 10 --keyword "LLM,Agent,GPT,RAG,Generative,Machine Learning" --deep | python3 -c "import json,sys; data=json.load(sys.stdin); print(f'HN items returned: {len(data)}')"

echo "--- Smoke test: v2ex ---"
python3 /workspace/scripts/fetch_news.py --source v2ex --limit 10 --keyword "LLM,Agent,GPT,RAG,Generative,Machine Learning" --deep | python3 -c "import json,sys; data=json.load(sys.stdin); print(f'V2EX items returned: {len(data)}')"

echo "=== Setup complete. Workspace ready for agent. ==="