#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying problem files exist..."
test -f /workspace/hr_system/candidates/2025/pending/resume_draft_chensiyuan.txt && echo "✓ Resume draft found"
test -f /workspace/hr_system/outbox/drafts/cooperation_email_draft.txt && echo "✓ Email draft found"
test -f /workspace/hr_system/internal/meeting_notes/digital_transformation_article_draft.txt && echo "✓ Article draft found"
test -f /workspace/hr_system/task_manifest.txt && echo "✓ Task manifest found"

echo "Setup complete."