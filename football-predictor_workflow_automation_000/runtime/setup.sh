#!/bin/bash
set -e

chmod -R 755 /workspace/scripts/
chmod 644 /workspace/config/leagues.json

echo "[setup] Workspace permissions configured."
echo "[setup] memory/ JSON state files are absent — agent must create them."
ls /workspace/memory/