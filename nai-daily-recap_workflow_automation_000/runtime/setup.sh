#!/usr/bin/env bash
set -e

echo "[setup] Setting permissions..."
chmod +x "${WORKSPACE}/scripts/nightly_recap.sh" 2>/dev/null || true

# Write the test date into a file the agent can read if it needs today's date
# (mirrors what cron would provide via environment or system clock)
echo "2025-06-10" > "${WORKSPACE}/.test_date"

echo "[setup] Environment ready. Test date: 2025-06-10"