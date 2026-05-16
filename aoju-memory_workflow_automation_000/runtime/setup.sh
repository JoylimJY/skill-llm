#!/bin/bash
set -e

# Make all memory scripts executable
chmod +x /workspace/mem_learn.py
chmod +x /workspace/mem_evolve.py
chmod +x /workspace/mem_recall.py
chmod +x /workspace/mem_status.py

echo "Scripts are executable."
echo "Workspace contents:"
find /workspace -type f | sort