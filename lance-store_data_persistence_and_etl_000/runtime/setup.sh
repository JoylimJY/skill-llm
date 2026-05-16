#!/bin/bash
set -e

cd /workspace
chmod +x scripts/command.py

# Verify the lance store is functional
python3 scripts/command.py list-datasets-info > /dev/null 2>&1 && echo "Lance store OK" || echo "Lance store check failed (may be OK if not yet initialized)"

echo "Setup complete."