#!/usr/bin/env bash
set -e

echo "=== Setting up workspace permissions ==="
chmod -R 755 /workspace

echo "=== Verifying reference files exist ==="
for f in \
  /workspace/references/graduation-and-planning-rules.md \
  /workspace/references/course-catalog.md \
  /workspace/references/required-bands-by-grade.md \
  /workspace/references/summer-school-catalog.md \
  /workspace/student_records/alex_chen_transcript.md \
  /workspace/admin/school_memos/catalog_update_aug2024.md; do
  if [ -f "$f" ]; then
    echo "  OK: $f"
  else
    echo "  MISSING: $f"
    exit 1
  fi
done

echo "=== Setup complete ==="