#!/usr/bin/env bash
set -e

cd /workspace/lobster

# Install the core lobster-ai stub in editable/development mode
# This makes `from lobster.xxx import yyy` work system-wide
pip install -e . --quiet -i https://pypi.tuna.tsinghua.edu.cn/simple

echo "Core lobster-ai stub installed."
echo "Workspace ready."