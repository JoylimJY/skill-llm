#!/bin/bash
set -e

# Ensure workspace directory exists
mkdir -p /workspace/reports

# Verify key reference files are in place
echo "Verifying workspace setup..."
for f in \
    /workspace/references/survey-free.json \
    /workspace/references/user-survey-free.json \
    /workspace/references/scoring.md \
    /workspace/references/personality-types.md \
    /workspace/agents/persona_library/nexus-assistant-3.json; do
    if [ ! -f "$f" ]; then
        echo "ERROR: Missing required file: $f"
        exit 1
    fi
done

echo "Workspace ready. All reference files present."