#!/bin/bash
set -e

chmod +x /workspace/scripts/parse_opml.py
chmod +x /workspace/scripts/build_digest.py

echo "[setup] Workspace ready. Scripts are executable."
echo "[setup] Key files:"
ls -la /workspace/scripts/
ls -la /workspace/assets/