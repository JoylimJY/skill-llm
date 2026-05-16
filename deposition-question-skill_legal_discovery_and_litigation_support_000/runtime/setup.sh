#!/usr/bin/env bash
set -e

# Make extraction script executable
chmod +x /workspace/scripts/extract_relativity_pages.py

# Verify PDFs were created
echo "=== Workspace PDF inventory ==="
find /workspace/productions -name "*.pdf" | sort

echo "=== Scripts ==="
ls /workspace/scripts/

echo "=== References ==="
ls /workspace/references/

echo "Setup complete."