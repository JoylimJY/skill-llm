#!/usr/bin/env bash
set -e

# Make all scripts executable
chmod +x /workspace/scripts/generate_newsletter.py
chmod +x /workspace/scripts/curate_content.py
chmod +x /workspace/scripts/add_affiliate_links.py
chmod +x /workspace/scripts/schedule_newsletter.py

# Install pytz explicitly just in case
pip install pytz -q -i https://pypi.tuna.tsinghua.edu.cn/simple

echo "[setup] All scripts are executable and dependencies are ready."
echo "[setup] Workspace is at /workspace"
ls /workspace/scripts/