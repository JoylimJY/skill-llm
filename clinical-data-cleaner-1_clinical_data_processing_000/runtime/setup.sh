#!/usr/bin/env bash
set -e

# Make the script executable
chmod +x /workspace/20260318/scientific-skills/Data\ Analytics/clinical-data-cleaner/scripts/main.py

# Verify the script compiles cleanly
cd "/workspace/20260318/scientific-skills/Data Analytics/clinical-data-cleaner"
python -m py_compile scripts/main.py
echo "Script syntax verified."
echo "Workspace ready."