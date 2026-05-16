#!/bin/bash
set -e

chmod +x /workspace/scripts/ebbinghaus.py

# Run initial decay so the strength values in memory_db.json are current
cd /workspace
python3 scripts/ebbinghaus.py decay > /dev/null 2>&1

echo "Setup complete. Ebbinghaus memory manager ready."