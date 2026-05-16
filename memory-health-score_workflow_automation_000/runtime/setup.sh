#!/bin/bash
set -e

# Make scripts executable
chmod +x /workspace/scripts/bootstrap.sh 2>/dev/null || true
chmod +x /workspace/scripts/compress_memory.py 2>/dev/null || true
chmod +x /workspace/scripts/rebuild_index.py 2>/dev/null || true

# Verify the workspace was set up correctly (silent check)
echo "Workspace ready."
echo "Files in workspace:"
find /workspace -type f | sort | head -40

# Print MEMORY.md line count for debugging
wc -l /workspace/MEMORY.md 2>/dev/null || true

# Print log file stats
echo "Log files:"
ls -la /workspace/memory/logs/ 2>/dev/null || true