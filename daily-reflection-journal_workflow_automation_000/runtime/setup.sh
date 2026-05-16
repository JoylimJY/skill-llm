#!/bin/bash
set -e

# Make scripts executable
chmod +x /workspace/scripts/export_journal.sh
chmod +x /workspace/scripts/word_count.py

echo "Setup complete. Workspace is ready."
echo "Current workspace structure:"
find /workspace -type f | sort