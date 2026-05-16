#!/bin/bash
set -e

# Make all skill scripts executable
find /workspace/skills -name "*.sh" -exec chmod +x {} \;

# Verify required memory files exist
echo "Verifying workspace integrity..."
for f in "memory/inner-state.json" "memory/habits.json" "memory/drive.json" "memory/SELF.md"; do
    if [ -f "/workspace/$f" ]; then
        echo "  [OK] $f"
    else
        echo "  [MISSING] $f — workspace generation may have failed"
        exit 1
    fi
done

# Verify diary entries exist
DIARY_COUNT=$(ls /workspace/memory/diary/*.md 2>/dev/null | wc -l)
echo "  [OK] diary entries found: $DIARY_COUNT"

echo "Setup complete."