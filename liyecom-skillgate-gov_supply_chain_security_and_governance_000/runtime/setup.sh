#!/bin/bash
set -e

echo "[setup] Warming up npm cache for skillgate package..."
# Pre-fetch the package to speed up agent execution
npx --yes @skillgate/openclaw-skillgate@0.1.3 --version 2>/dev/null || true

echo "[setup] Setting permissions..."
chmod -R 755 /workspace/enterprise-skills

echo "[setup] Workspace ready."
ls -la /workspace/
ls -la /workspace/enterprise-skills/