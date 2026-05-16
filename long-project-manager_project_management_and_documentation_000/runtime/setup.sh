#!/usr/bin/env bash
set -euo pipefail

# Make monitoring script executable (realistic)
chmod +x /workspace/scripts/monitoring/check_replication_lag.sh 2>/dev/null || true

echo "Sandbox ready."
echo "Workspace contents:"
find /workspace -maxdepth 3 -type f | sort