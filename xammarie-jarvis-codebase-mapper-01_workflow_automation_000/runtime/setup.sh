#!/usr/bin/env bash
set -e

# Make scripts executable
chmod +x /workspace/scripts/migrate_ledger.sh 2>/dev/null || true

# Create a simple PYTHONPATH entry so imports resolve during eval
export PYTHONPATH=/workspace:$PYTHONPATH
echo "export PYTHONPATH=/workspace:\$PYTHONPATH" >> /etc/environment

echo "Setup complete."