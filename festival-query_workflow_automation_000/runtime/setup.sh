#!/bin/bash
set -e

chmod +x /workspace/scripts/festival_query.py

# Verify the tool runs
python3 /workspace/scripts/festival_query.py --terms 2025 > /dev/null 2>&1 && echo "festival_query.py is functional" || echo "WARNING: festival_query.py check failed"

echo "Setup complete."