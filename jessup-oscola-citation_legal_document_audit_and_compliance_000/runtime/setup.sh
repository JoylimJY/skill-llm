#!/bin/bash
set -e

# Ensure workspace permissions
chmod -R 755 /workspace

# Confirm main brief exists
if [ -f "/workspace/jessup_2024/briefs/applicant/applicant_memorial_draft.txt" ]; then
    echo "[SETUP] Main brief file confirmed present."
else
    echo "[SETUP ERROR] Main brief file missing!"
    exit 1
fi

echo "[SETUP] Sandbox ready. Agent task begins."