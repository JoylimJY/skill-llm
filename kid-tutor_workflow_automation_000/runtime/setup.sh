#!/bin/bash
set -e

# Make scripts executable
chmod +x /workspace/scripts/manage_profile.py
chmod +x /workspace/scripts/generate_report.py

echo "[setup] Scripts are executable."
echo "[setup] Workspace ready."
ls -la /workspace/scripts/