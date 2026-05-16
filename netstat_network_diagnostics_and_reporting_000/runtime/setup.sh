#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${WORKSPACE:-/workspace}"

echo "[setup] Ensuring scripts/script.sh is executable..."
chmod +x "${WORKSPACE}/scripts/script.sh"

echo "[setup] Creating netstat data directory..."
mkdir -p "$HOME/.local/share/netstat"

echo "[setup] Environment ready."
echo "  WORKSPACE=${WORKSPACE}"
echo "  HOME=${HOME}"
echo "  Data dir: $HOME/.local/share/netstat"