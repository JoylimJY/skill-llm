#!/bin/bash
set -e

echo "[setup] Setting workspace permissions..."
chmod -R 755 /workspace

echo "[setup] Verifying key files exist..."
ls /workspace/MEMORY.md
ls /workspace/memory/index.json
ls /workspace/memory/archive.md

echo "[setup] Setup complete. Ready for agent."