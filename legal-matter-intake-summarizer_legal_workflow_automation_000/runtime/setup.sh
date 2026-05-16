#!/usr/bin/env bash
set -e

SKILL_DIR="/workspace/skills/legal-matter-intake-summarizer"

# Ensure run.py is executable
chmod +x "$SKILL_DIR/scripts/run.py"

# Verify the skill structure is intact
echo "[setup] Verifying skill structure..."
for f in \
    "$SKILL_DIR/scripts/run.py" \
    "$SKILL_DIR/resources/spec.json" \
    "$SKILL_DIR/resources/template.md" \
    "$SKILL_DIR/examples/sample_input.txt" \
    "$SKILL_DIR/tests/smoke-test.md"; do
    if [ -f "$f" ]; then
        echo "[setup] OK: $f"
    else
        echo "[setup] MISSING: $f"
        exit 1
    fi
done

echo "[setup] Skill environment ready."
echo "[setup] Messy intake file: /workspace/case-files/incoming/lin_intake_raw_notes_20240115.txt"