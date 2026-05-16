#!/usr/bin/env bash
set -e

# Freeze the original mtime of all READ-ONLY reference files so eval can detect tampering
for f in \
    /workspace/SKILL.md \
    /workspace/references/checklist.md \
    /workspace/references/principles.md \
    /workspace/references/patterns.md \
    /workspace/references/anti-patterns.md \
    /workspace/references/templates.md \
    /workspace/references/structure.md; do
    # Record SHA256 of each read-only file into a hidden manifest
    sha256sum "$f" >> /workspace/.readonly_manifest.sha256
done

# Record original content of learnings.md so eval can diff it
cp /workspace/references/learnings.md /workspace/.learnings_original.md

echo "Setup complete. Read-only manifest written to /workspace/.readonly_manifest.sha256"