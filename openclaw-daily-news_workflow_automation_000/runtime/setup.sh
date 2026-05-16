#!/bin/bash
set -e

chmod +x /workspace/scripts/generate_report_content.py
chmod +x /workspace/scripts/search_openclaw_news.py

echo "Workspace setup complete."
echo "Agent task: Process data/raw/news_items_2026-03-15.json and generate the daily report."