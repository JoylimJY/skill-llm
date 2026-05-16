#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying skill files exist..."
ls /workspace/skills/do-it/SKILL.md
ls /workspace/skills/do-it/GUNGUN-FAMILY-2.0.md
ls /workspace/cases/pending/case_002_career_decision.md

echo "Setup complete. Agent should read SKILL.md and process the pending case."