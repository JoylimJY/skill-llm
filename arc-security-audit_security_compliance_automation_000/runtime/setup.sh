#!/usr/bin/env bash
set -euo pipefail

# Ensure audit.py is executable
chmod +x /workspace/openclaw-security-audit/scripts/audit.py

# Verify the skill directories are in place
echo "=== Skill directories ==="
ls -1 /root/.openclaw/skills/

# Verify audit.py is runnable
echo "=== Smoke-test audit.py help ==="
python3 /workspace/openclaw-security-audit/scripts/audit.py --help || true

echo "Setup complete."