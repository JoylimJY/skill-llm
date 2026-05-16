#!/usr/bin/env bash
set -euo pipefail

echo "[setup] Making CLI scripts executable..."
chmod +x /workspace/omni-skill/src/cli/omni_packager.py
chmod +x /workspace/omni-skill/src/cli/omni_ctl.py
chmod +x /workspace/omni-skill/src/gateway/gateway.py

echo "[setup] Verifying workspace structure..."
ls /workspace/
ls /workspace/omni-skill/src/cli/
ls /workspace/raw_plugins/text_classifier/

echo "[setup] Workspace ready."