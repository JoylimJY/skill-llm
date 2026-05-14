#!/usr/bin/env bash
set -e

chmod +x /workspace/scripts/sqlite_cli.py

# Ensure sqlite_connector is importable from workspace root and scripts/
cp /workspace/sqlite_connector.py /workspace/scripts/sqlite_connector.py

echo "Setup complete. Workspace ready."
ls /workspace/scripts/