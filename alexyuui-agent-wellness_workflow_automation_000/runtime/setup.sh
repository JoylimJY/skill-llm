#!/bin/bash
set -e

echo "[setup] Workspace ready. No background services needed."

# Ensure workspace permissions are correct
chmod -R 755 /workspace

echo "[setup] Done."