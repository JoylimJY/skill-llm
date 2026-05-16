#!/usr/bin/env bash
set -e

# Ensure output directories exist and are writable
mkdir -p /workspace/outputs/runs
mkdir -p /workspace/outputs/reports
mkdir -p /workspace/logs

# Verify key input files are present
echo "[setup] Checking workspace structure..."
test -f /workspace/config/agentdojo.config.yaml && echo "  [OK] config found"
test -d /workspace/config/drills && echo "  [OK] drills dir found"
test -f /workspace/templates/daily-report-template.md && echo "  [OK] template found"
test -f /workspace/docs/scoring-rubric.md && echo "  [OK] rubric found"
test -f /workspace/docs/threat-model.md && echo "  [OK] threat-model found"

echo "[setup] Workspace ready."