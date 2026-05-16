#!/usr/bin/env bash
set -e

chmod +x /workspace/scripts/main.py

# Verify the script compiles cleanly
python -m py_compile /workspace/scripts/main.py
echo "[setup] scripts/main.py compiled OK"

# Smoke test
python /workspace/scripts/main.py --value 100 --from-unit mg_dl --to-unit mmol_l --analyte glucose
echo "[setup] smoke test passed"