#!/usr/bin/env bash
set -e

echo "[setup] Workspace ready. No background services needed."
echo "[setup] Contents of /workspace:"
find /workspace -type f | sort