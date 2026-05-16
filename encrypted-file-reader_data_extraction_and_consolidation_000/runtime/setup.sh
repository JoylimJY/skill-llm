#!/usr/bin/env bash
set -e

# Make the skill script executable
chmod +x /skills/encrypted-file-reader/read_file.py

# Verify the skill script is in place
if [ ! -f /skills/encrypted-file-reader/read_file.py ]; then
    echo "ERROR: read_file.py not found at /skills/encrypted-file-reader/read_file.py"
    exit 1
fi

# Verify source data files are in place
if [ ! -f /workspace/corporate_data/Q3_2024/budget.xlsx ]; then
    echo "ERROR: budget.xlsx not found"
    exit 1
fi
if [ ! -f /workspace/corporate_data/Q3_2024/meeting_minutes.docx ]; then
    echo "ERROR: meeting_minutes.docx not found"
    exit 1
fi
if [ ! -f /workspace/corporate_data/Q3_2024/access_log.csv ]; then
    echo "ERROR: access_log.csv not found"
    exit 1
fi

echo "Setup complete. Skill script and source files are ready."