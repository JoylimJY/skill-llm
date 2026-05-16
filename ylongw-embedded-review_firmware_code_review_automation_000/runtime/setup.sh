#!/usr/bin/env bash
set -e

chmod +x /workspace/scripts/prepare-diff.sh

# Verify git repo is in good shape
cd /workspace/firmware-nfc
git log --oneline | head -5

echo "[setup] Workspace initialized. Diff size:"
git diff HEAD~1..HEAD --stat
echo "[setup] Done."