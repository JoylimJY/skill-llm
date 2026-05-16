#!/bin/bash
set -e

# Make setup script executable
chmod +x /workspace/scripts/setup.py

echo "[setup] Workspace ready. Vault at /workspace/PharmaVault"
echo "[setup] Setup script at /workspace/scripts/setup.py"
tree /workspace --charset=ascii 2>/dev/null || find /workspace -type f | head -40