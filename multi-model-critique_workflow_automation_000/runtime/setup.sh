#!/usr/bin/env bash
set -euo pipefail

# Make scripts executable
chmod +x /workspace/skills/multi-model-critique/scripts/build_round_prompts.py
chmod +x /workspace/skills/multi-model-critique/scripts/run_orchestration.py

# Ensure output directories exist
mkdir -p /workspace/projects/hospital-protocol-review/processed
mkdir -p /workspace/skills/multi-model-critique/outputs/drafts
mkdir -p /workspace/skills/multi-model-critique/outputs/critiques
mkdir -p /workspace/skills/multi-model-critique/outputs/revisions

echo "Setup complete. Workspace ready."
echo "Skill directory: /workspace/skills/multi-model-critique"
echo "Project data: /workspace/projects/hospital-protocol-review/raw/"