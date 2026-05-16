#!/usr/bin/env bash
set -e

echo "[setup] Making all scripts executable..."
chmod +x /app/scripts/*.py

echo "[setup] Verifying Python version..."
python3 --version

echo "[setup] Verifying scripts exist..."
ls -la /app/scripts/

echo "[setup] Workspace structure:"
find /app -type f | sort

echo "[setup] Setup complete."