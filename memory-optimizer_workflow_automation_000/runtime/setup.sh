#!/bin/bash
set -e

# Ensure scripts are executable
chmod +x /workspace/scripts/memory-dedup.py
chmod +x /workspace/scripts/memory-watcher.py
chmod +x /workspace/scripts/memory-archive.sh

echo "Setup complete. Workspace is ready."
echo "Memory directory contents:"
ls -la /workspace/memory/
echo ""
echo "Current index keys (should include stale entry):"
python3 -c "
import json
from pathlib import Path
idx = json.loads(Path('/workspace/memory/.index.json').read_text())
print(list(idx.keys()))
print(f'Total entries in stale index: {len(idx)}')
"