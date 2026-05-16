#!/usr/bin/env bash
set -euo pipefail

# Ensure scripts are executable
chmod +x /workspace/scripts/fetch_news.py

# Ensure reports directory exists and is writable
mkdir -p /workspace/reports
chmod 777 /workspace/reports

# Ensure cache directory exists
mkdir -p /workspace/cache
chmod 777 /workspace/cache

echo "Setup complete. Workspace ready."
ls -la /workspace/