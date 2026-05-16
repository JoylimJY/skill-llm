#!/bin/bash
set -e

echo "=== Setting up patient-records-api workspace ==="

cd /workspace

# Make migration script executable
chmod +x scripts/migrate.sh 2>/dev/null || true

echo "=== Workspace ready ==="
echo "Directory structure:"
find /workspace/src -type f | sort