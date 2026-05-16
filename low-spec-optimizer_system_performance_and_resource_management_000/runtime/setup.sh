#!/usr/bin/env bash
set -e

WORKSPACE="${WORKSPACE:-/workspace}"

# Ensure mock scripts are executable (belt-and-suspenders)
chmod +x "${WORKSPACE}/skill-dir/scripts/check_resources.sh"
chmod +x "${WORKSPACE}/skill-dir/scripts/cleanup_sessions.sh"

# Ensure the invocation log starts clean
rm -f /tmp/cleanup_invocations.log
touch /tmp/cleanup_invocations.log

echo "[setup] Mock scripts ready."
echo "[setup] Cleanup invocation log cleared."