#!/bin/bash
set -e

# Make scripts executable
chmod +x /workspace/scripts/run_tests.sh 2>/dev/null || true

echo "[setup] Workspace ready. BOOTSTRAP.md exists: $(test -f /workspace/BOOTSTRAP.md && echo YES || echo NO)"
echo "[setup] SOUL.override.md exists: $(test -f /workspace/SOUL.override.md && echo YES || echo NO)"
echo "[setup] Today's date: $(date +%Y-%m-%d)"