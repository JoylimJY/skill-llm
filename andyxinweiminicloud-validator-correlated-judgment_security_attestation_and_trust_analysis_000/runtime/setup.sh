#!/bin/bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace

# Verify key input files exist
echo "Verifying workspace setup..."
for f in \
    "/workspace/validators/validator-a/metadata.json" \
    "/workspace/validators/validator-b/metadata.json" \
    "/workspace/validators/validator-c/metadata.json" \
    "/workspace/attestation/results/edge_case_verdicts.csv" \
    "/workspace/attestation/edge_cases/evasion_transferability.json" \
    "/workspace/traces/validator-a/evaluation_traces.json" \
    "/workspace/traces/validator-b/evaluation_traces.json" \
    "/workspace/traces/validator-c/evaluation_traces.json" \
    "/workspace/TASK_BRIEF.txt"; do
    if [ -f "$f" ]; then
        echo "  [OK] $f"
    else
        echo "  [MISSING] $f"
        exit 1
    fi
done

echo "Workspace verified. Agent may begin."