#!/bin/bash
set -e

WORKSPACE=/workspace

# Make scripts executable
chmod +x "$WORKSPACE/scripts/generate-pdf.js" 2>/dev/null || true

# Verify key reference files exist
for f in \
  "$WORKSPACE/references/score-band-table.md" \
  "$WORKSPACE/references/error-taxonomy.md" \
  "$WORKSPACE/references/538-keywords-guide.md" \
  "$WORKSPACE/references/review-style-guide.md" \
  "$WORKSPACE/assets/review-template.html" \
  "$WORKSPACE/sessions/progress_history.json" \
  "$WORKSPACE/sessions/cambridge17/c17t2p3_raw_input.txt"; do
  if [ ! -f "$f" ]; then
    echo "ERROR: Missing required file: $f"
    exit 1
  fi
done

echo "Setup complete. All reference files verified."
echo "Workspace ready for agent task."