#!/usr/bin/env bash
set -e

# Make scripts executable
chmod +x /workspace/scripts/init_nika_skill.py
chmod +x /workspace/scripts/validate_nika_skill.py

# Ensure skills dir exists
mkdir -p /workspace/skills

echo "=== Workspace ready ==="
echo "Skill to create: 章节连贯性审查"
echo "Run: python3 scripts/init_nika_skill.py '章节连贯性审查'"
echo "Then fill in README.md and create sub-docs."
echo "Then validate: python3 scripts/validate_nika_skill.py 'skills/章节连贯性审查'"