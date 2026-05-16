#!/usr/bin/env bash
set -e

chmod +x /workspace/skill-creator-course-outline/scripts/run.py

echo "[setup] Workspace ready."
echo "[setup] Skill directory: /workspace/skill-creator-course-outline"
echo "[setup] Project notes:   /workspace/projects/vertical-farming-course/raw_notes/"
tree /workspace --dirsfirst -L 4 2>/dev/null || find /workspace -maxdepth 4 | sort