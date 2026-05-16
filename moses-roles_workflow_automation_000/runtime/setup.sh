#!/usr/bin/env bash
set -euo pipefail

# Ensure audit_stub.py is executable
chmod +x ~/.openclaw/workspace/skills/moses-governance/scripts/audit_stub.py

# Ensure governance dir exists with correct permissions
mkdir -p ~/.openclaw/governance
chmod 755 ~/.openclaw/governance

# Verify Python3 can run the audit stub without errors (smoke test)
python3 ~/.openclaw/workspace/skills/moses-governance/scripts/audit_stub.py log \
    --action "setup_check" \
    --detail "sandbox initialized" \
    --agent "system" 2>&1 || true

echo "[setup] Sandbox initialization complete."
echo "[setup] Governance dir: $(ls -la ~/.openclaw/governance/)"