#!/usr/bin/env bash
set -e

# Make the run.py script executable
chmod +x /workspace/skills/meeting-risk-radar/scripts/run.py

echo "[setup] Permissions set on run.py"

# Verify the skill structure is intact
echo "[setup] Verifying skill structure..."
for f in \
    "/workspace/skills/meeting-risk-radar/scripts/run.py" \
    "/workspace/skills/meeting-risk-radar/resources/spec.json" \
    "/workspace/skills/meeting-risk-radar/resources/template.md" \
    "/workspace/skills/meeting-risk-radar/tests/smoke-test.md" \
    "/workspace/meetings/2024-Q4/board/board_compliance_meeting.json"
do
    if [ -f "$f" ]; then
        echo "[setup] OK: $f"
    else
        echo "[setup] MISSING: $f" >&2
        exit 1
    fi
done

echo "[setup] All checks passed. Sandbox ready."