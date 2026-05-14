#!/usr/bin/env bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace

# Confirm key input files are present
echo "[setup] Verifying workspace structure..."
test -f /workspace/references/regulation-check-workflow.md && echo "[OK] workflow reference found"
test -f /workspace/operations/incident_logs/incident_log_2025Q2.json && echo "[OK] incident log found"
test -d /workspace/regulations/active && echo "[OK] active regulations directory found"

echo "[setup] Workspace ready."