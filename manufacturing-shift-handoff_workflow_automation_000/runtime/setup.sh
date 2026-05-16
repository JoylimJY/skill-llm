#!/usr/bin/env bash
set -e

SKILL_DIR="/workspace/skills/manufacturing-shift-handoff"

# Make run.py executable
chmod +x "$SKILL_DIR/scripts/run.py"

# Verify key files exist
echo "=== Setup verification ==="
echo "[✓] spec.json:    $(ls -lh $SKILL_DIR/resources/spec.json)"
echo "[✓] template.md:  $(ls -lh $SKILL_DIR/resources/template.md)"
echo "[✓] run.py:       $(ls -lh $SKILL_DIR/scripts/run.py)"
echo "[✓] Input log:    $(ls -lh /workspace/plant_data/raw_logs/night_shift_20240619.txt)"
echo "=== Setup complete ==="