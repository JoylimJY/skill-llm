#!/bin/bash
set -e

echo "[setup] Setting permissions..."
chmod +x /workspace/tools/budget_engine.py

# Verify budget_engine.py is runnable
echo "[setup] Verifying budget_engine.py..."
python3 /workspace/tools/budget_engine.py --method A --revenue 48.3 --industry manufacturing > /tmp/engine_test.json
if [ $? -eq 0 ]; then
    echo "[setup] budget_engine.py OK"
    cat /tmp/engine_test.json
else
    echo "[setup] ERROR: budget_engine.py failed"
    exit 1
fi

# Also verify confidence calculation
python3 /workspace/tools/budget_engine.py --confidence --sources_json '[{"type":"financial_report","weight":1.0},{"type":"bid_record","weight":0.8},{"type":"job_posting","weight":0.5}]' > /tmp/conf_test.json
echo "[setup] Confidence test:"
cat /tmp/conf_test.json

echo "[setup] All setup complete. Workspace ready."
ls -la /workspace/