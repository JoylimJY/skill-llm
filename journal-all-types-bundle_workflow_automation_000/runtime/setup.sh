#!/bin/bash
set -e

# Make the render script executable
chmod +x /workspace/journal-submission-radar/scripts/render_journal_dossier.py

# Verify key resource files exist
echo "=== Verifying workspace structure ==="
ls /workspace/journal-submission-radar/resources/
ls /workspace/journal-submission-radar/scripts/

# Verify Python can run the render script (help check)
python3 /workspace/journal-submission-radar/scripts/render_journal_dossier.py --help 2>/dev/null || true

echo "=== Setup complete ==="
echo "Skill base directory: /workspace/journal-submission-radar"