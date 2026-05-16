#!/bin/bash
set -e

chmod +x /workspace/create_excel.py
chmod +x /workspace/create_word.py
chmod +x /workspace/ods.py
chmod +x /workspace/scheduler.py
chmod +x /workspace/skills/_core/autonomous.py

echo "[setup] office-hub workspace ready."
echo "[setup] Proprietary scripts are executable."
ls -la /workspace/*.py