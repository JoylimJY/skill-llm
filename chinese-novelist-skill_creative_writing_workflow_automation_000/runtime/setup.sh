#!/usr/bin/env bash
set -e

# Make the wordcount script executable
chmod +x /workspace/scripts/check_chapter_wordcount.py

# Verify Python can run the script
python /workspace/scripts/check_chapter_wordcount.py --help 2>/dev/null || true

echo "Setup complete. Workspace ready."
echo "Key resources:"
echo "  - /workspace/scripts/check_chapter_wordcount.py"
echo "  - /workspace/references/ (all template files)"
echo "  - /workspace/platform/submission/editorial_brief.txt"