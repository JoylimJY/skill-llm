#!/bin/bash
set -euo pipefail

# ── Make git-manager available on PATH ────────────────────────────────────────
chmod +x /workspace/bin/git-manager
export PATH="/workspace/bin:$PATH"

# Add to global profile so any shell session has it
echo 'export PATH="/workspace/bin:$PATH"' >> /etc/profile
echo 'export PATH="/workspace/bin:$PATH"' >> /root/.bashrc

# ── Create log directory for git-manager ─────────────────────────────────────
mkdir -p /root/.openclaw/logs
touch /root/.openclaw/logs/git-manager.log

# ── Ensure git identity is set ────────────────────────────────────────────────
git config --global user.email "agent@testenv.local"
git config --global user.name "Test Agent"
git config --global init.defaultBranch main

# ── Verify the mock binary is callable ───────────────────────────────────────
echo "[setup] Verifying git-manager is executable..."
/workspace/bin/git-manager --action status --repo /workspace/pharma-compliance-system
echo "[setup] git-manager smoke test passed."

echo "[setup] Setup complete. Repo ready at /workspace/pharma-compliance-system"
echo "[setup] Untracked/unstaged files:"
git -C /workspace/pharma-compliance-system status --short