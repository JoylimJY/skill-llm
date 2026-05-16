#!/usr/bin/env bash
set -e

# Make run.py executable
chmod +x /workspace/skills/changelog-curator/scripts/run.py

echo "[setup] Workspace ready."
echo "[setup] Skill root: /workspace/skills/changelog-curator"
echo "[setup] Raw input:  /workspace/project/docs/raw_v2.4.0_commits.txt"