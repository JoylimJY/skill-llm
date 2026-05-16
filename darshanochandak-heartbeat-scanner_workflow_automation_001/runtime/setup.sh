#!/bin/bash
set -e

chmod +x /workspace/heartbeat_scanner.py

echo "=== Workspace contents ==="
find /workspace -type f | sort

echo ""
echo "=== Setup complete ==="
echo "Task: See /workspace/data_exports/CMP-2024-0847_brief.txt"