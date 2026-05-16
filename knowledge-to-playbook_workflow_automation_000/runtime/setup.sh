#!/usr/bin/env bash
set -euo pipefail

# Make run.py executable
chmod +x /workspace/skills/knowledge-to-playbook/scripts/run.py

# Verify the skill directory structure is intact
echo "[setup] Verifying skill bundle layout..."
for f in \
    /workspace/skills/knowledge-to-playbook/scripts/run.py \
    /workspace/skills/knowledge-to-playbook/resources/spec.json \
    /workspace/skills/knowledge-to-playbook/resources/template.md \
    /workspace/skills/knowledge-to-playbook/tests/smoke-test.md \
    /workspace/data/oncall_notes/db_cleanup_slack_export.txt; do
    if [ -f "$f" ]; then
        echo "[setup] ✓ $f"
    else
        echo "[setup] ✗ MISSING: $f"
        exit 1
    fi
done

echo "[setup] Workspace ready."