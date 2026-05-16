#!/bin/bash
set -e

# Ensure target directory exists and is writable
mkdir -p /Users/aibin/.openclaw/workspace
chmod -R 777 /Users/aibin/.openclaw

# Ensure workspace is ready
chmod -R 755 /workspace

echo "Setup complete. Target directory: /Users/aibin/.openclaw/workspace"
echo "Roster input: /workspace/hr/new_staff_notice.txt"
echo "Correction memo: /workspace/hr/correction_memo.txt"