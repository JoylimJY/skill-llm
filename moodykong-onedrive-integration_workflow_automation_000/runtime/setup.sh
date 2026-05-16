#!/usr/bin/env bash
set -e

echo "[setup] Ensuring copy_to_onedrive.py is executable..."
chmod +x ~/.openclaw/skills/onedrive-integration/scripts/copy_to_onedrive.py
chmod +x ~/.openclaw/skills/onedrive-integration/scripts/onboard.sh

echo "[setup] Verifying Python3 is available..."
python3 --version

echo "[setup] Workspace structure:"
find /workspace -type f | sort

echo "[setup] Skill structure:"
find ~/.openclaw -type f | sort

echo "[setup] Setup complete."