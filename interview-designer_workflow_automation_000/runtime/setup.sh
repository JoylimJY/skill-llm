#!/bin/bash
set -e

# Make skills readable
chmod 644 /workspace/skills/SKILL.md
chmod 644 /workspace/templates/interview_guide_template.md

# Make all candidate/hiring files readable
find /workspace -name "*.md" -exec chmod 644 {} \;

echo "Setup complete. Workspace ready."
echo ""
echo "Key files available:"
echo "  /workspace/skills/SKILL.md                                    -- skill definition"
echo "  /workspace/templates/interview_guide_template.md              -- output template"
echo "  /workspace/hiring/vp_computational_biology/job_description.md -- JD"
echo "  /workspace/candidates/active/wei_chen_resume.md               -- candidate resume"