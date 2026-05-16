#!/bin/bash
set -e

# Define paths
SKILL_DIR="/workspace/.openclaw/workspace/skills/mood-logger/scripts"
OBSIDIAN_TARGET="/workspace/obsidian_vault/05-Daily"

# Make scripts executable
chmod +x "$SKILL_DIR/log_mood.py"
chmod +x "$SKILL_DIR/weekly_mood_report.py"
chmod +x "$SKILL_DIR/send_weekly_report.py"

# Patch SAVE_DIR in log_mood.py and weekly_mood_report.py to point to our local vault
HARDCODED_PATH="/mnt/c/Users/loong/iCloudDrive/iCloud~md~obsidian/HomeMo.Art/05-Daily"

sed -i "s|SAVE_DIR = \"${HARDCODED_PATH}\"|SAVE_DIR = \"${OBSIDIAN_TARGET}\"|g" \
    "$SKILL_DIR/log_mood.py"

sed -i "s|SAVE_DIR = \"${HARDCODED_PATH}\"|SAVE_DIR = \"${OBSIDIAN_TARGET}\"|g" \
    "$SKILL_DIR/weekly_mood_report.py"

# Verify patch worked
if grep -q "${OBSIDIAN_TARGET}" "$SKILL_DIR/log_mood.py"; then
    echo "✅ log_mood.py patched successfully"
else
    echo "❌ Patch failed for log_mood.py"
    exit 1
fi

if grep -q "${OBSIDIAN_TARGET}" "$SKILL_DIR/weekly_mood_report.py"; then
    echo "✅ weekly_mood_report.py patched successfully"
else
    echo "❌ Patch failed for weekly_mood_report.py"
    exit 1
fi

# Create home directory symlink so ~/.openclaw resolves correctly
mkdir -p /root
ln -sfn /workspace/.openclaw /root/.openclaw

echo "✅ Setup complete. Vault at: ${OBSIDIAN_TARGET}"