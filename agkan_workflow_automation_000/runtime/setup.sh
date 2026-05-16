#!/bin/bash
set -e

echo "=== Setting up agkan workspace ==="

cd /workspace

# Ensure .agkan directory exists for the database
mkdir -p .agkan

# Initialize agkan database by running a benign command
agkan task list > /dev/null 2>&1 || true

echo "=== agkan initialized ==="
echo "Database path: /workspace/.agkan/data.db"

# Make deploy scripts executable (distractor)
chmod +x scripts/deploy/rollback.sh 2>/dev/null || true

# Verify agkan is working
agkan task count --json && echo "agkan is operational"

echo "=== Setup complete ==="