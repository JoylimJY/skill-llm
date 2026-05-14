#!/usr/bin/env bash
set -euo pipefail

echo "[setup] Making all skill scripts executable..."
chmod +x /workspace/agent-guardrails/scripts/*.sh
chmod +x /workspace/agent-guardrails/assets/pre-commit-hook

echo "[setup] Verifying project git repo..."
git -C /workspace/paycorp-service status --short || true

echo "[setup] Workspace layout:"
find /workspace -maxdepth 3 -type f | sort

echo "[setup] Ready. Agent should start from /workspace."