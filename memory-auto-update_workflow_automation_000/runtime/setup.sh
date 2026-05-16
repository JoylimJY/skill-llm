#!/bin/bash
set -e

echo "[setup] Making scripts executable..."
chmod +x /workspace/skills/memory-auto-update/scripts/user_settings.py
chmod +x /workspace/skills/memory-auto-update/scripts/extract_memory.py
chmod +x /workspace/skills/memory-auto-update/scripts/generate_summary.py
chmod +x /workspace/skills/memory-auto-update/scripts/write_memory.py

echo "[setup] Verifying script integrity..."
python3 /workspace/skills/memory-auto-update/scripts/user_settings.py --show
echo "[setup] user_settings.py OK"

echo "[setup] Setup complete. Workspace is ready."