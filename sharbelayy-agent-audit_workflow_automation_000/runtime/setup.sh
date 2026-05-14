#!/usr/bin/env bash
set -e

chmod +x /workspace/scripts/audit.py

echo "=== Meridian FinOps AI Audit Sandbox ==="
echo "Workspace ready at /workspace"
echo "OpenClaw config: /workspace/.openclaw/openclaw.json"
echo "Cron history:    /workspace/.openclaw/cron/history/"
echo "References:      /workspace/references/"
echo ""
echo "The audit.py stub is intentionally non-functional."
echo "Implement the audit logic based on the skill documentation."