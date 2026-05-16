#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${WORKSPACE:-/workspace}"

# Make the mealplan script executable
chmod +x "${WORKSPACE}/scripts/script.sh"

# Initialize the mealplan data directory
mkdir -p "${HOME}/.local/share/mealplan"

echo "[setup] mealplan script is ready."
echo "[setup] Data directory: ${HOME}/.local/share/mealplan"
echo "[setup] Script path: ${WORKSPACE}/scripts/script.sh"