#!/bin/bash
set -e

chmod +x /workspace/tools/scripts/convert_notes.sh 2>/dev/null || true

echo "Workspace ready. Key files:"
echo "  /workspace/topic_outline.txt        — CS302 topic outline (agent's main input)"
echo "  /workspace/intake_params.txt         — Intake parameters"
echo "  /workspace/rules/                    — Skill rule files"
echo ""
echo "Expected outputs (agent must create):"
echo "  study-notes.md"
echo "  quick-reference.md"
echo "  exam-qa.md"