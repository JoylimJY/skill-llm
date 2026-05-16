#!/usr/bin/env bash
set -e

# Make the run.py script executable
chmod +x /workspace/skills/creator-campaign-planner/scripts/run.py

# Verify critical skill files exist
echo "[setup] Checking skill resources..."
for f in \
    /workspace/skills/creator-campaign-planner/scripts/run.py \
    /workspace/skills/creator-campaign-planner/resources/spec.json \
    /workspace/skills/creator-campaign-planner/resources/template.md \
    /workspace/skills/creator-campaign-planner/examples/example_input.json \
    /workspace/skills/creator-campaign-planner/tests/smoke-test.md \
    /workspace/campaign_briefs/luminescent_q4_brief.txt; do
    if [ -f "$f" ]; then
        echo "[OK] $f"
    else
        echo "[MISSING] $f"
    fi
done

echo "[setup] Environment ready."