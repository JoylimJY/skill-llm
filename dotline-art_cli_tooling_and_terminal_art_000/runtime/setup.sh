#!/usr/bin/env bash
set -e

# Ensure the skill script is executable
chmod +x /workspace/skills/dotline-art/scripts/dotline_art.py

# Verify pypinyin is importable (sanity check)
python3 -c "from pypinyin import lazy_pinyin; print('pypinyin OK')"

echo "Setup complete."