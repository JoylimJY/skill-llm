#!/usr/bin/env bash
set -e

# Ensure all skill scripts are executable
find /workspace/skills -name "*.py" -exec chmod +x {} \;

echo "[SETUP] Skill scripts ready."
echo "[SETUP] Vault contents:"
find /workspace/pkm_vault -type f | sort

echo ""
echo "[SETUP] Sandbox ready. Agent may begin."