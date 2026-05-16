#!/usr/bin/env bash
set -euo pipefail

echo "[setup] Workspace ready. No background services required."
echo "[setup] Listing workspace structure:"
find /workspace -type f | sort
echo "[setup] Done."