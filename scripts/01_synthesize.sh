#!/bin/bash
# Continue on errors so all skills get attempted
total=0; success=0; failed=0
for skill_dir in anthropic-skills/*/; do
    skill=$(basename "$skill_dir")
    total=$((total+1))
    # Check if 6 instances already exist for this skill
    existing=$(ls -d instances/${skill}_* 2>/dev/null | wc -l)
    if [ "$existing" -ge 6 ]; then
        echo "SKIP (already have $existing instances): $skill"
        success=$((success+1))
        continue
    fi
    echo "=== Synthesizing: $skill (6 instances) ==="
    if uv run python -m src.run synthesize --skill-dir "$skill_dir" --num 6; then
        success=$((success+1))
    else
        echo "FAILED: $skill"
        failed=$((failed+1))
    fi
done
echo "=== Synthesis complete: $success/$total skills succeeded, $failed failed ==="
ls instances/ | wc -l
