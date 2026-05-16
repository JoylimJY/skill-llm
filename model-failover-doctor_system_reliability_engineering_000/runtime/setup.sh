#!/usr/bin/env bash
set -e

echo "[setup] Setting permissions on doctor script..."
chmod +x /root/.openclaw/workspace/skills/model-failover-doctor/model_failover_doctor.py

echo "[setup] Verifying workspace structure..."
ls /root/.openclaw/workspace/config/
ls /root/.openclaw/workspace/sessions/
ls /root/.openclaw/runtime/injectors/

echo "[setup] Workspace ready. Broken configs in place."
echo "[setup] Gateway log evidence:"
grep "All models failed" /root/.openclaw/workspace/logs/gateway.log || true