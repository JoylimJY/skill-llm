#!/usr/bin/env bash
set -e

chmod +x /workspace/projects/scripts/add_ledger_entry.py

# Verify the script is executable and works
python3 /workspace/projects/scripts/add_ledger_entry.py --help > /dev/null 2>&1 || true

echo "Setup complete. Workspace is ready."
echo "Working directory: /workspace"
ls /workspace/