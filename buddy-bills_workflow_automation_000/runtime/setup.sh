#!/usr/bin/env bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace/finance-records/
chmod 644 /workspace/inbox_may2025.txt

echo "Setup complete. Workspace ready for agent."