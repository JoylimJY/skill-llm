#!/usr/bin/env bash
set -euo pipefail

SKILL_ROOT="/workspace/20260318/scientific-skills/Evidence Insight/key-takeaways"

# Ensure scripts are executable
chmod +x "${SKILL_ROOT}/scripts/main.py"

# Confirm the packaged script parses cleanly (smoke test)
python -m py_compile "${SKILL_ROOT}/scripts/main.py"
echo "[setup] py_compile OK"

echo "[setup] Workspace ready."