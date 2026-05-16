#!/bin/bash
set -e

# Make the decision tracker script executable
chmod +x /workspace/scripts/decision_tracker.py

# Verify the workspace structure
echo "=== Workspace structure ==="
find /workspace -type f -not -path "*/__pycache__/*" | sort

echo ""
echo "=== Verifying decision_tracker.py is runnable ==="
cd /workspace && python scripts/decision_tracker.py --demo

echo ""
echo "=== Current decisions.md state ==="
cat /workspace/memory/board-meetings/decisions.md

echo ""
echo "=== Meeting brief available at ==="
echo "/workspace/memory/board-meetings/2026-04-28-meeting-brief.md"

echo ""
echo "Setup complete."