#!/bin/bash
set -e

# Make the brain script executable
chmod +x /workspace/scripts/brain.py

# Verify Python can find the script
python3 /workspace/scripts/brain.py --help > /dev/null 2>&1 || true

echo "[setup] Workspace ready. Brain script is executable."
echo "[setup] Incident report is available at /workspace/INCIDENT_REPORT.txt"
echo "[setup] Run: python3 scripts/brain.py init to start"