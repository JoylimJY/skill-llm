#!/usr/bin/env bash
set -e

# Make audit script executable
chmod +x /workspace/scripts/context_cleanup_audit.py

# Create the default state dir that the skill references
mkdir -p /root/.openclaw/sessions
mkdir -p /root/.openclaw/state

echo "[setup] State dir created at /root/.openclaw"
echo "[setup] Workspace ready at /workspace"
echo "[setup] Audit script is executable."