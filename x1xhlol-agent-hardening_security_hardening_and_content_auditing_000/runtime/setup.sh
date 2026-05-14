#!/bin/bash
set -e

# Ensure scripts are executable
chmod +x /workspace/scripts/maintenance/cleanup_logs.sh 2>/dev/null || true

# Verify the input dataset was generated
if [ ! -f "/workspace/pipeline/ingestion/raw/batch_20240303.json" ]; then
    echo "[setup] ERROR: Input dataset not found. Run gen_inputs_script first."
    exit 1
fi

echo "[setup] Workspace initialized. Input dataset present."
echo "[setup] Agent task: process pipeline/ingestion/raw/batch_20240303.json"
echo "[setup] Expected output: audit/threat_report.json"