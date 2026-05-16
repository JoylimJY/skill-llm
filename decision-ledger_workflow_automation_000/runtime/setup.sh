#!/usr/bin/env bash
set -e

# Make the run.py script executable
chmod +x /workspace/skills/decision-ledger/scripts/run.py

# Verify key files exist
echo "=== Verifying workspace structure ==="
ls /workspace/skills/decision-ledger/scripts/
ls /workspace/skills/decision-ledger/resources/
ls /workspace/skills/decision-ledger/examples/
ls /workspace/skills/decision-ledger/tests/
ls /workspace/project/infra-phase2/meetings/

echo "=== spec.json preview ==="
python3 -c "import json; s=json.load(open('/workspace/skills/decision-ledger/resources/spec.json')); print('Sections:', [x['label'] for x in s['output_sections']])"

echo "=== Workspace ready ==="