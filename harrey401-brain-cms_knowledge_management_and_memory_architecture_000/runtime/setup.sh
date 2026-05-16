#!/usr/bin/env bash
set -e

# Make all memory_brain scripts executable
chmod +x /workspace/memory_brain/index_memory.py
chmod +x /workspace/memory_brain/query_memory.py
chmod +x /workspace/memory_brain/nrem.py
chmod +x /workspace/memory_brain/rem.py

# Set up a Python virtual environment inside memory_brain (as per Brain CMS spec)
cd /workspace/memory_brain
python3 -m venv .venv
.venv/bin/pip install lancedb numpy pyarrow requests --quiet -i https://pypi.tuna.tsinghua.edu.cn/simple

echo "Setup complete. memory_brain/.venv ready."
echo "Workspace layout:"
find /workspace -not -path '*/\.*' -not -path '*/vectorstore/*' | sort | head -60