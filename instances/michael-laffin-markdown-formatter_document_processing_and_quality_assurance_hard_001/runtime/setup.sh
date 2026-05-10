#!/usr/bin/env bash
set -euo pipefail

echo "=== Setup: Installing skill dependencies ==="
cd /workspace/skill_context
npm install
echo "=== Skill dependencies installed ==="

echo "=== Setup complete ==="