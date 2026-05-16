#!/bin/bash
set -e

# Ensure workspace is accessible
chmod -R 755 /workspace

# Verify the decision log was created
if [ -f "/workspace/pipeline/reasoning_engine/logs/decision_snapshot_20240915.json" ]; then
    echo "[OK] Decision snapshot log found."
    ENTRY_COUNT=$(python3 -c "import json; d=json.load(open('/workspace/pipeline/reasoning_engine/logs/decision_snapshot_20240915.json')); print(len(d['decision_log']))")
    echo "[OK] Decision log contains ${ENTRY_COUNT} entries."
else
    echo "[ERROR] Decision snapshot log missing!"
    exit 1
fi

echo "[SETUP COMPLETE] Sandbox ready for agent evaluation."