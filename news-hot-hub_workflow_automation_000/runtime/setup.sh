#!/bin/bash
set -e

chmod +x /workspace/news-hot-hub/scripts/hub.py
chmod +x /workspace/news-hot-hub/scripts/zhihu.py
chmod +x /workspace/news-hot-hub/scripts/toutiao.py
chmod +x /workspace/news-hot-hub/scripts/aibase.py

# Verify the scripts are functional
python /workspace/news-hot-hub/scripts/hub.py status > /dev/null 2>&1 && echo "hub.py status: OK" || echo "hub.py status: WARNING"

echo "Setup complete."