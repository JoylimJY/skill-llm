#!/usr/bin/env bash
set -e

# Ensure workspace permissions
chmod -R 755 /workspace

# Verify critical files exist
echo "[setup] Verifying workspace..."
[ -f /workspace/SKILL.md ] && echo "[OK] SKILL.md" || echo "[WARN] SKILL.md missing"
[ -f /workspace/templates/interview_guide_template.md ] && echo "[OK] template" || echo "[WARN] template missing"
[ -f /workspace/candidates/quantum_hoe_2024/resume_priya_venkataraman.txt ] && echo "[OK] resume" || echo "[WARN] resume missing"
[ -f /workspace/candidates/quantum_hoe_2024/job_description.txt ] && echo "[OK] JD" || echo "[WARN] JD missing"

echo "[setup] Workspace ready."